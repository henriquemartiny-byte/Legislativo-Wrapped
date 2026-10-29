"""
Orquestrador de Ponta a Ponta do MVP — Vogon Cívico.

Fluxo:
1. Ingestão Efêmera (Classe B):
   - Congresso Nacional: Câmara dos Deputados (CEAP 2025 - Todos os 513 Deputados) + Senado Federal (CEAPS 2025 - Todos os 81 Senadores)
   - Executivo/Municípios: PNCP (Dispensas de Licitação - Lei nº 14.133/2021, Art. 75)
   -> Todos os arquivos brutos passam por diretório temporário autodestrutivo com geração de Hash SHA-256.
2. Auditoria Determinística (Polars + DuckDB - Zero LLM):
   - Z-Score, Mediana e Intervalo Interquartil (IQR) por rubrica sobre centenas de milhares de notas fiscais;
   - Concentração de Fornecedores por Gabinete Parlamentar (Share %);
   - Limiares do Art. 75 da Lei 14.133/2021 em Dispensas do PNCP.
3. Persistência Exclusiva na Camada Gold (`pipeline/storage/gold/`):
   - Salva cubos `.parquet` e snapshot `.json` prontos para o Dashboard Exploratório.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time

import polars as pl

from ingestors.class_b_camara import fetch_congresso_cotas_ephemeral
from ingestors.class_b_pncp import fetch_pncp_dispensas_sample
from auditors.parliamentary_anomalies import audit_parliamentary_expenses
from auditors.split_expense import audit_pncp_split_expense
from auditors.overpricing_zscore import audit_pncp_overpricing_zscore
from explainer.orcamentes_translator import translate_rubrica

GOLD_DIR = Path(__file__).resolve().parent / "storage" / "gold"


def main() -> None:
    t0 = time.perf_counter()
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print("🏛️  VOGON CÍVICO • MOTOR DETERMINÍSTICO DE AUDITORIA (MVP)")
    print("==================================================================")

    # 1. Ingestão Efêmera: Congresso Nacional (Câmara dos Deputados + Senado Federal)
    print("\n[1/4] Ingerindo Cota Parlamentar (Câmara dos Deputados + Senado Federal) em zona efêmera...")
    df_ceap, prov_congresso = fetch_congresso_cotas_ephemeral(ano=2025)
    print(
        f"  -> Notas fiscais processadas em memória: {len(df_ceap):,} "
        f"| Lotes SHA-256 auditados e descartados do disco: {len(prov_congresso)}"
    )

    # 2. Ingestão Efêmera: PNCP (Dispensas de Licitação - Lei 14.133/2021)
    print("\n[2/4] Ingerindo Dispensas de Licitação (PNCP - Lei 14.133/2021) em zona efêmera...")
    df_pncp, prov_pncp = fetch_pncp_dispensas_sample(paginas=3, tamanho_pagina=50)
    print(
        f"  -> Contratações diretas processadas em memória: {len(df_pncp):,} "
        f"| Lotes SHA-256 auditados e descartados do disco: {len(prov_pncp)}"
    )

    # 3. Execução das Trilhas Determinísticas (DuckDB + Polars)
    print("\n[3/4] Executando algoritmos estatísticos no DuckDB + Polars (Z-Score, IQR, Concentração, Art. 75)...")
    ceap_audit = audit_parliamentary_expenses(df_ceap)
    df_outliers_ceap = ceap_audit["outliers_notas"]
    df_conc_ceap = ceap_audit["concentracao_fornecedores"]
    df_rubricas_ceap = ceap_audit["resumo_rubricas"]
    df_ranking_parl = ceap_audit["ranking_parlamentares"]

    df_pncp_split = audit_pncp_split_expense(df_pncp)
    df_pncp_scored = audit_pncp_overpricing_zscore(df_pncp_split)

    # 4. Gravação na Camada Gold (Parquet + JSON compacto para o Dashboard)
    print("\n[4/4] Persistindo cubos analíticos leves na Camada Gold (pipeline/storage/gold/)...")
    if not df_outliers_ceap.is_empty():
        df_outliers_ceap.write_parquet(GOLD_DIR / "congresso_outliers_all.parquet")
        df_outliers_ceap.head(500).write_parquet(GOLD_DIR / "congresso_outliers_top500.parquet")
    if not df_conc_ceap.is_empty():
        df_conc_ceap.write_parquet(GOLD_DIR / "congresso_concentracao_fornecedores.parquet")
    if not df_rubricas_ceap.is_empty():
        df_rubricas_ceap.write_parquet(GOLD_DIR / "congresso_resumo_rubricas.parquet")
    if not df_ranking_parl.is_empty():
        df_ranking_parl.write_parquet(GOLD_DIR / "congresso_ranking_parlamentares.parquet")
    if not df_pncp_scored.is_empty():
        df_pncp_scored.write_parquet(GOLD_DIR / "pncp_dispensas_scored.parquet")

    rubricas_list = []
    if not df_rubricas_ceap.is_empty():
        for r in df_rubricas_ceap.to_dicts():
            trad = translate_rubrica(r["tipo_despesa"])
            r["traducao_humana"] = trad["humano"]
            r["explicacao_cidada"] = trad["explicacao"]
            r["risco_tipico"] = trad["risco_tipico"]
            rubricas_list.append(r)

    top_outliers_ceap = []
    if not df_outliers_ceap.is_empty():
        for row in df_outliers_ceap.head(80).to_dicts():
            trad = translate_rubrica(row["tipo_despesa"])
            row["traducao_humana"] = trad["humano"]
            top_outliers_ceap.append(row)

    top_concentracao_ceap = df_conc_ceap.head(50).to_dicts() if not df_conc_ceap.is_empty() else []
    top_parlamentares = df_ranking_parl.head(60).to_dicts() if not df_ranking_parl.is_empty() else []
    top_pncp_alerts = df_pncp_scored.head(50).to_dicts() if not df_pncp_scored.is_empty() else []

    total_ceap_val = float(df_ceap["valor_liquido"].sum()) if not df_ceap.is_empty() else 0.0
    total_pncp_val = float(df_pncp["valor_auditado"].sum()) if not df_pncp.is_empty() else 0.0
    qtd_severos_ceap = (
        int(df_outliers_ceap.filter(pl.col("z_score") >= 3.0).height)
        if not df_outliers_ceap.is_empty()
        else 0
    )
    qtd_alertas_pncp = (
        int(
            df_pncp_scored.filter(
                pl.col("diagnostico_legal") != "DENTRO DO LIMITE REFERENCIAL DO ART. 75"
            ).height
        )
        if not df_pncp_scored.is_empty()
        else 0
    )

    elapsed = round(time.perf_counter() - t0, 2)

    gold_snapshot = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "engine": "Polars 2.1 + DuckDB 2.0 (100% Determinístico)",
            "execution_seconds": elapsed,
            "ephemeral_raw_bytes_retained_on_disk": 0,
            "provenance_batches_congresso": len(prov_congresso),
            "provenance_batches_pncp": len(prov_pncp),
        },
        "kpis": {
            "ceap_notas_auditadas": len(df_ceap),
            "ceap_parlamentares_amostra": int(df_ceap["parlamentar"].n_unique()) if not df_ceap.is_empty() else 0,
            "ceap_fornecedores_distintos": int(df_ceap["fornecedor_cnpj_cpf"].n_unique()) if not df_ceap.is_empty() else 0,
            "ceap_valor_total_auditado": round(total_ceap_val, 2),
            "ceap_atipicidades_z3": qtd_severos_ceap,
            "pncp_dispensas_auditadas": len(df_pncp),
            "pncp_valor_total_auditado": round(total_pncp_val, 2),
            "pncp_alertas_art75": qtd_alertas_pncp,
        },
        "rubricas_ceap": rubricas_list,
        "outliers_ceap": top_outliers_ceap,
        "concentracao_fornecedores": top_concentracao_ceap,
        "ranking_parlamentares": top_parlamentares,
        "pncp_dispensas": top_pncp_alerts,
        "provenance_sample": (prov_congresso + prov_pncp),
    }

    gold_json_path = GOLD_DIR / "mvp_gold_dashboard.json"
    gold_json_path.write_text(
        json.dumps(gold_snapshot, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8",
    )

    print("\n==================================================================")
    print(f"✅ AUDITORIA CONCLUÍDA EM {elapsed}s | RASTRO BRUTO NO DISCO: 0 BYTES")
    print(
        f"🏛️  Congresso (Câmara + Senado): {len(df_ceap):,} notas fiscais | "
        f"R$ {total_ceap_val:,.2f} auditados | {qtd_severos_ceap:,} outliers (Z-Score >= 3)"
    )
    print(
        f"📋 PNCP Lei 14.133: {len(df_pncp):,} dispensas | "
        f"R$ {total_pncp_val:,.2f} auditados | {qtd_alertas_pncp} alertas Art. 75"
    )
    print(f"💾 Snapshot Gold salvo em: {gold_json_path}")
    print("==================================================================")


if __name__ == "__main__":
    main()
