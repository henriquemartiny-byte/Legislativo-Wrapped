"""
Trilha 2 — Detecção Determinística de Outliers Estatísticos em Contratações Diretas (PNCP).

Calcula Z-Score, Mediana e Múltiplo sobre a Mediana por enquadramento legal no PNCP.
"""

import duckdb
import polars as pl


def audit_pncp_overpricing_zscore(df_pncp_audited: pl.DataFrame) -> pl.DataFrame:
    """
    Adiciona métricas estatísticas (Z-Score e Múltiplo da Mediana Nacional da Amostra)
    às contratações diretas coletadas no PNCP.
    """
    if df_pncp_audited.is_empty():
        return pl.DataFrame()

    con = duckdb.connect(":memory:")
    con.register("pncp_input", df_pncp_audited)

    scored = con.sql(
        """
        WITH stats AS (
            SELECT
                MEDIAN(valor_auditado) AS mediana_geral,
                AVG(valor_auditado) AS media_geral,
                COALESCE(STDDEV_SAMP(valor_auditado), 1.0) AS std_geral,
                QUANTILE_CONT(valor_auditado, 0.75) - QUANTILE_CONT(valor_auditado, 0.25) AS iqr_geral
            FROM pncp_input
        )
        SELECT
            p.*,
            ROUND(s.mediana_geral, 2) AS mediana_amostra_pncp,
            ROUND((p.valor_auditado - s.media_geral) / NULLIF(s.std_geral, 0), 2) AS z_score_pncp,
            ROUND(p.valor_auditado / NULLIF(s.mediana_geral, 0), 2) AS multiplo_mediana_pncp
        FROM pncp_input p
        CROSS JOIN stats s
        ORDER BY p.valor_auditado DESC
        """
    ).pl()

    return scored
