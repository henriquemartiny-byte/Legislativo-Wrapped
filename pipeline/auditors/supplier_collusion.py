"""
Trilha 3 — Padrões de Fornecedores, Concentração Transversal e Risco Societário (Multi-Gabinete / Multi-Órgão).

Identifica fornecedores (CNPJs) que concentram simultaneamente verbas de múltiplos parlamentares
(Câmara + Senado) ou múltiplos órgãos públicos, preparando a lista de CNPJs prioritários
para o cruzamento remoto de QSA e CEIS/CNEP via BigQuery (`class_a_bigquery.py`).
"""

import duckdb
import polars as pl


def audit_cross_cabinet_suppliers(df_ceap: pl.DataFrame) -> pl.DataFrame:
    """
    Detecta fornecedores que atendem múltiplos gabinetes parlamentares ou recebem
    os maiores volumes agregados na Cota Parlamentar (CEAP + CEAPS), excluindo
    concessionárias aéreas ou estatais de utilidade pública quando filtrável.
    """
    if df_ceap.is_empty():
        return pl.DataFrame()

    con = duckdb.connect(":memory:")
    con.register("ceap_raw", df_ceap)

    return con.sql(
        """
        SELECT
            fornecedor_cnpj_cpf,
            ANY_VALUE(fornecedor_nome) AS fornecedor_nome,
            ANY_VALUE(tipo_despesa) AS rubrica_predominante,
            COUNT(DISTINCT parlamentar) AS qtd_parlamentares_atendidos,
            COUNT(DISTINCT partido) AS qtd_partidos_atendidos,
            COUNT(DISTINCT uf) AS qtd_ufs_atendidas,
            COUNT(*) AS qtd_notas_emitidas,
            ROUND(SUM(valor_liquido), 2) AS valor_total_recebido,
            ROUND(AVG(valor_liquido), 2) AS ticket_medio_nota,
            ROUND(MAX(valor_liquido), 2) AS maior_nota_emitida,
            MAX(url_documento) AS exemplo_url_documento,
            ANY_VALUE(source_sha256) AS source_sha256
        FROM ceap_raw
        WHERE LENGTH(REGEXP_REPLACE(fornecedor_cnpj_cpf, '[^0-9]', '', 'g')) = 14
          AND tipo_despesa NOT ILIKE '%PASSAG%'
          AND tipo_despesa NOT ILIKE '%TELEFONIA%'
        GROUP BY fornecedor_cnpj_cpf
        ORDER BY valor_total_recebido DESC
        LIMIT 100
        """
    ).pl()

