"""
Auditor Determinístico — Gastos Parlamentares (CEAP Câmara dos Deputados & CEAPS Senado Federal).

Executa 100% em Polars + DuckDB (Zero LLM):
1. Cálculo de Z-Score, Mediana e Intervalo Interquartil (IQR) por Casa Legislativa e Rubrica de Despesa;
2. Cálculo de Concentração de Fornecedor por Gabinete (Share % e HHI);
3. Ranking de Parlamentares e Fornecedores por volume auditado e atipicidades estatísticas.
"""

import duckdb
import polars as pl


def audit_parliamentary_expenses(df_ceap: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """
    Recebe DataFrame normalizado de notas fiscais parlamentares (Câmara + Senado) e retorna:
    - 'outliers_notas': Notas fiscais com maior desvio estatístico (Z-Score / IQR) na respectiva rubrica;
    - 'concentracao_fornecedores': Pares (Parlamentar, Fornecedor) com alta concentração de verba;
    - 'resumo_rubricas': Estatísticas descritivas por rubrica (Mediana, Média, Q1, Q3, IQR, Total);
    - 'ranking_parlamentares': Resumo por parlamentar com qtd de notas, valor total e qtd de outliers.
    """
    if df_ceap.is_empty():
        return {
            "outliers_notas": pl.DataFrame(),
            "concentracao_fornecedores": pl.DataFrame(),
            "resumo_rubricas": pl.DataFrame(),
            "ranking_parlamentares": pl.DataFrame(),
        }

    con = duckdb.connect(":memory:")
    con.register("ceap_raw", df_ceap)

    # 1. Resumo estatístico por Casa + Rubrica (tipo_despesa)
    resumo_rubricas = con.sql(
        """
        SELECT
            casa_legislativa,
            tipo_despesa,
            COUNT(*) AS qtd_notas,
            COUNT(DISTINCT parlamentar) AS qtd_parlamentares,
            COUNT(DISTINCT fornecedor_cnpj_cpf) AS qtd_fornecedores,
            ROUND(SUM(valor_liquido), 2) AS valor_total,
            ROUND(AVG(valor_liquido), 2) AS media_nota,
            ROUND(MEDIAN(valor_liquido), 2) AS mediana_nota,
            ROUND(QUANTILE_CONT(valor_liquido, 0.25), 2) AS q1,
            ROUND(QUANTILE_CONT(valor_liquido, 0.75), 2) AS q3,
            ROUND(QUANTILE_CONT(valor_liquido, 0.75) - QUANTILE_CONT(valor_liquido, 0.25), 2) AS iqr,
            ROUND(COALESCE(STDDEV_SAMP(valor_liquido), 0.0), 2) AS desvio_padrao,
            ROUND(MAX(valor_liquido), 2) AS maior_nota
        FROM ceap_raw
        GROUP BY casa_legislativa, tipo_despesa
        HAVING COUNT(*) >= 10
        ORDER BY valor_total DESC
        """
    ).pl()

    con.register("rubrica_stats", resumo_rubricas)

    # 2. Detecção determinística de Outliers de Nota Fiscal (Z-Score + Múltiplo da Mediana + Regra de Tukey IQR)
    outliers_notas = con.sql(
        """
        WITH scored AS (
            SELECT
                c.casa_legislativa,
                c.parlamentar_id,
                c.parlamentar,
                c.partido,
                c.uf,
                c.tipo_despesa,
                c.fornecedor_nome,
                c.fornecedor_cnpj_cpf,
                c.num_documento,
                c.data_documento,
                ROUND(c.valor_liquido, 2) AS valor_liquido,
                c.url_documento,
                c.source_sha256,
                s.mediana_nota,
                s.media_nota,
                s.desvio_padrao,
                s.iqr,
                s.q3,
                CASE
                    WHEN s.desvio_padrao > 0 THEN ROUND((c.valor_liquido - s.media_nota) / s.desvio_padrao, 2)
                    ELSE 0.0
                END AS z_score,
                CASE
                    WHEN s.mediana_nota > 0 THEN ROUND(c.valor_liquido / s.mediana_nota, 2)
                    ELSE 1.0
                END AS multiplo_mediana,
                CASE
                    WHEN s.iqr > 0 THEN ROUND((c.valor_liquido - s.q3) / s.iqr, 2)
                    ELSE 0.0
                END AS desvio_iqr
            FROM ceap_raw c
            JOIN rubrica_stats s
              ON c.casa_legislativa = s.casa_legislativa
             AND c.tipo_despesa = s.tipo_despesa
        )
        SELECT
            *,
            CASE
                WHEN z_score >= 3.0 AND multiplo_mediana >= 5.0
                    THEN 'ATIPICIDADE ESTATÍSTICA SEVERA (Z-Score >= 3 e >= 5x Mediana)'
                WHEN z_score >= 2.0 OR multiplo_mediana >= 4.0
                    THEN 'ATIPICIDADE ESTATÍSTICA MODERADA (Acima da Faixa Interquartil)'
                ELSE 'DENTRO DO PADRÃO ESTATÍSTICO DA RUBRICA'
            END AS classificacao_auditoria
        FROM scored
        WHERE z_score >= 2.0 OR multiplo_mediana >= 4.0
        ORDER BY z_score DESC, valor_liquido DESC
        """
    ).pl()

    con.register("outliers_view", outliers_notas)

    # 3. Concentração de Fornecedor por Gabinete (Share % do Fornecedor no Total Anual do Parlamentar)
    concentracao_fornecedores = con.sql(
        """
        WITH total_parlamentar AS (
            SELECT
                casa_legislativa,
                parlamentar_id,
                parlamentar,
                partido,
                uf,
                SUM(valor_liquido) AS total_gabinete,
                COUNT(*) AS total_notas_gabinete
            FROM ceap_raw
            GROUP BY casa_legislativa, parlamentar_id, parlamentar, partido, uf
            HAVING SUM(valor_liquido) >= 50000
        ),
        por_fornecedor AS (
            SELECT
                casa_legislativa,
                parlamentar_id,
                parlamentar,
                fornecedor_nome,
                fornecedor_cnpj_cpf,
                ANY_VALUE(tipo_despesa) AS rubrica_principal,
                COUNT(*) AS qtd_notas_fornecedor,
                SUM(valor_liquido) AS total_fornecedor,
                MAX(url_documento) AS exemplo_url_documento,
                ANY_VALUE(source_sha256) AS source_sha256
            FROM ceap_raw
            WHERE fornecedor_cnpj_cpf != ''
            GROUP BY casa_legislativa, parlamentar_id, parlamentar, fornecedor_nome, fornecedor_cnpj_cpf
        )
        SELECT
            t.casa_legislativa,
            t.parlamentar_id,
            t.parlamentar,
            t.partido,
            t.uf,
            f.fornecedor_nome,
            f.fornecedor_cnpj_cpf,
            f.rubrica_principal,
            f.qtd_notas_fornecedor,
            ROUND(f.total_fornecedor, 2) AS total_fornecedor,
            ROUND(t.total_gabinete, 2) AS total_gabinete,
            ROUND((f.total_fornecedor / NULLIF(t.total_gabinete, 0)) * 100.0, 1) AS share_percentual,
            f.exemplo_url_documento,
            f.source_sha256,
            CASE
                WHEN (f.total_fornecedor / NULLIF(t.total_gabinete, 0)) >= 0.60
                    THEN 'CONCENTRAÇÃO ELEVADA DE FORNECEDOR (>= 60% da cota do gabinete em único CNPJ)'
                WHEN (f.total_fornecedor / NULLIF(t.total_gabinete, 0)) >= 0.40
                    THEN 'CONCENTRAÇÃO MODERADA DE FORNECEDOR (40% a 60% em único CNPJ)'
                ELSE 'PULVERIZAÇÃO REGULAR'
            END AS alerta_concentracao
        FROM por_fornecedor f
        JOIN total_parlamentar t
          ON f.casa_legislativa = t.casa_legislativa
         AND f.parlamentar = t.parlamentar
        WHERE f.total_fornecedor > 0
        ORDER BY f.total_fornecedor DESC
        """
    ).pl()

    # 4. Ranking de Parlamentares por Volume Auditado + Quantidade de Outliers
    ranking_parlamentares = con.sql(
        """
        WITH base_parl AS (
            SELECT
                casa_legislativa,
                parlamentar_id,
                parlamentar,
                partido,
                uf,
                COUNT(*) AS qtd_notas,
                COUNT(DISTINCT fornecedor_cnpj_cpf) AS qtd_fornecedores,
                ROUND(SUM(valor_liquido), 2) AS total_gasto,
                ROUND(MAX(valor_liquido), 2) AS maior_nota_individual,
                ROUND(MEDIAN(valor_liquido), 2) AS mediana_nota_parlamentar
            FROM ceap_raw
            GROUP BY casa_legislativa, parlamentar_id, parlamentar, partido, uf
        ),
        out_parl AS (
            SELECT
                casa_legislativa,
                parlamentar,
                COUNT(*) AS qtd_outliers_z3,
                ROUND(MAX(z_score), 2) AS max_z_score
            FROM outliers_view
            WHERE z_score >= 3.0
            GROUP BY casa_legislativa, parlamentar
        )
        SELECT
            b.*,
            COALESCE(o.qtd_outliers_z3, 0) AS qtd_outliers_z3,
            COALESCE(o.max_z_score, 0.0) AS max_z_score
        FROM base_parl b
        LEFT JOIN out_parl o
          ON b.casa_legislativa = o.casa_legislativa
         AND b.parlamentar = o.parlamentar
        ORDER BY b.total_gasto DESC
        """
    ).pl()

    return {
        "outliers_notas": outliers_notas,
        "concentracao_fornecedores": concentracao_fornecedores,
        "resumo_rubricas": resumo_rubricas,
        "ranking_parlamentares": ranking_parlamentares,
    }
