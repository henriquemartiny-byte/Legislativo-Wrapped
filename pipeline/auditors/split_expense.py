"""
Trilha 1 — Detecção Determinística de Fracionamento e Limites de Dispensa (Lei nº 14.133/2021, Art. 75).

Verifica dispensas de licitação no PNCP agrupadas por Órgão + Amparo Legal:
- Teto Art. 75, I (Obras/Engenharia/Manutenção de Veículos): R$ 119.812,02 (Decreto 11.871/2023 / atualizado)
- Teto Art. 75, II (Outros Serviços e Compras): R$ 59.906,02
"""

import duckdb
import polars as pl

TETO_ART_75_INCISO_I = 119812.02
TETO_ART_75_INCISO_II = 59906.02


def audit_pncp_split_expense(df_pncp: pl.DataFrame) -> pl.DataFrame:
    """
    Agrupa dispensas de licitação por Órgão e Unidade Gestora e avalia proximidade ou
    extrapolação dos referenciais do Art. 75 da Lei nº 14.133/2021.
    """
    if df_pncp.is_empty():
        return pl.DataFrame()

    con = duckdb.connect(":memory:")
    con.register("pncp_raw", df_pncp)

    result = con.sql(
        f"""
        WITH base AS (
            SELECT
                *,
                CASE
                    WHEN amparo_legal_nome ILIKE '%inciso I%' AND amparo_legal_nome NOT ILIKE '%inciso II%'
                        THEN {TETO_ART_75_INCISO_I}
                    ELSE {TETO_ART_75_INCISO_II}
                END AS teto_legal_referencia
            FROM pncp_raw
        ),
        orgao_agg AS (
            SELECT
                orgao_cnpj,
                COUNT(*) AS qtd_dispensas_janela,
                ROUND(SUM(valor_auditado), 2) AS soma_dispensas_orgao
            FROM base
            GROUP BY orgao_cnpj
        )
        SELECT
            b.numero_controle_pncp,
            b.orgao_cnpj,
            b.orgao_nome,
            b.unidade_nome,
            b.uf,
            b.municipio,
            b.amparo_legal_nome,
            b.amparo_legal_desc,
            b.objeto_compra,
            b.data_publicacao,
            ROUND(b.valor_auditado, 2) AS valor_auditado,
            b.teto_legal_referencia,
            ROUND((b.valor_auditado / b.teto_legal_referencia) * 100.0, 1) AS percentual_do_teto,
            o.qtd_dispensas_janela,
            o.soma_dispensas_orgao,
            b.pncp_portal_url,
            b.source_sha256,
            CASE
                WHEN b.valor_auditado > b.teto_legal_referencia
                    AND (b.amparo_legal_nome ILIKE '%inciso I%' OR b.amparo_legal_nome ILIKE '%inciso II%')
                    THEN 'ALERTA DE CONFORMIDADE: Valor individual acima do referencial Art. 75 I/II (Verificar Exceção Legal)'
                WHEN o.qtd_dispensas_janela >= 2 AND o.soma_dispensas_orgao > b.teto_legal_referencia
                    THEN 'INDÍCIO DE ACÚMULO DE DISPENSAS NA MESMA UNIDADE GESTORA'
                WHEN b.valor_auditado >= (b.teto_legal_referencia * 0.90)
                    AND b.valor_auditado <= b.teto_legal_referencia
                    THEN 'DISPENSA NO LIMIAR DO TETO LEGAL (90% a 100% do limite Art. 75)'
                ELSE 'DENTRO DO LIMITE REFERENCIAL DO ART. 75'
            END AS diagnostico_legal
        FROM base b
        JOIN orgao_agg o ON b.orgao_cnpj = o.orgao_cnpj
        ORDER BY b.valor_auditado DESC
        """
    ).pl()

    return result
