"""
Conector Efêmero Classe B — Portal Nacional de Contratações Públicas (PNCP - Lei 14.133/2021).

Consome a API REST Pública de Consultas do PNCP:
https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao

Ciclo: Baixa em pasta temporária -> Gera Hash SHA-256 -> Normaliza em Polars -> Auto-deleta brutos.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import httpx
import polars as pl

from core.ephemeral_workspace import ephemeral_ingestion_zone, compute_audit_provenance

PNCP_CONSULTA_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"


def fetch_pncp_dispensas_sample(
    paginas: int = 3,
    tamanho_pagina: int = 50,
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    """
    Coleta contratações diretas (Dispensas de Licitação - Modalidade 8 na Lei 14.133/2021)
    diretamente da API oficial do PNCP em janela recente.
    Retorna DataFrame Polars normalizado e registros de proveniência SHA-256.
    """
    provenance_records: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []

    headers = {"Accept": "application/json", "User-Agent": "VogonCivicoAuditEngine/0.1"}

    # Tenta janela recente (ou fallback para janela consolidada de 2025/2024 caso o relógio local esteja em 2026)
    candidate_windows = [
        ("20250201", "20250228"),
        ("20241101", "20241130"),
    ]
    now = datetime.now()
    if now.year <= 2025:
        dt_fim = now.strftime("%Y%m%d")
        dt_ini = (now - timedelta(days=25)).strftime("%Y%m%d")
        candidate_windows.insert(0, (dt_ini, dt_fim))

    with ephemeral_ingestion_zone("pncp_dispensas") as tmp_dir:
        with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as client:
            for data_inicial, data_final in candidate_windows:
                for pagina in range(1, paginas + 1):
                    # codigoModalidadeContratacao=8 -> Dispensa de Licitação (Lei 14.133/2021)
                    url = (
                        f"{PNCP_CONSULTA_URL}"
                        f"?dataInicial={data_inicial}&dataFinal={data_final}"
                        f"&codigoModalidadeContratacao=8"
                        f"&pagina={pagina}&tamanhoPagina={tamanho_pagina}"
                    )
                    try:
                        resp = client.get(url)
                        if resp.status_code != 200:
                            break
                        raw_bytes = resp.content
                        payload = resp.json()
                        data_list = payload.get("data") or []
                        if not data_list:
                            break

                        raw_file = tmp_dir / f"pncp_dispensas_{data_inicial}_p{pagina}.json"
                        raw_file.write_bytes(raw_bytes)
                        prov = compute_audit_provenance(raw_bytes, url)
                        provenance_records.append(prov)

                        for item in data_list:
                            val_estimado = float(item.get("valorTotalEstimado") or 0.0)
                            val_homologado = float(item.get("valorTotalHomologado") or 0.0)
                            val_ref = val_homologado if val_homologado > 0 else val_estimado
                            if val_ref <= 0:
                                continue

                            orgao_ent = item.get("orgaoEntidade") or {}
                            unidade_org = item.get("unidadeOrgao") or {}
                            amparo = item.get("amparoLegal") or {}

                            cnpj_orgao = str(orgao_ent.get("cnpj") or "")
                            ano_compra = int(item.get("anoCompra") or 2025)
                            seq_compra = int(item.get("sequencialCompra") or 1)
                            numero_controle = str(item.get("numeroControlePNCP") or "")

                            pncp_portal_url = (
                                f"https://pncp.gov.br/app/editais/{cnpj_orgao}/{ano_compra}/{seq_compra}"
                                if cnpj_orgao
                                else "https://pncp.gov.br"
                            )

                            rows.append(
                                {
                                    "numero_controle_pncp": numero_controle,
                                    "orgao_cnpj": cnpj_orgao,
                                    "orgao_nome": (orgao_ent.get("razaoSocial") or "ÓRGÃO NÃO INFORMADO").strip(),
                                    "esfera": str(orgao_ent.get("esferaId") or "N/A"),
                                    "poder": str(orgao_ent.get("poderId") or "N/A"),
                                    "unidade_nome": (unidade_org.get("nomeUnidade") or "").strip(),
                                    "uf": (unidade_org.get("ufSigla") or "BR").strip(),
                                    "municipio": (unidade_org.get("municipioNome") or "Nacional").strip(),
                                    "modalidade": (item.get("modalidadeNome") or "Dispensa de Licitação").strip(),
                                    "modo_disputa": (item.get("modoDisputaNome") or "").strip(),
                                    "amparo_legal_nome": (amparo.get("nome") or "Lei 14.133/2021 - Art. 75").strip(),
                                    "amparo_legal_desc": (amparo.get("descricao") or "").strip(),
                                    "objeto_compra": (item.get("objetoCompra") or "").strip(),
                                    "processo": str(item.get("processo") or ""),
                                    "data_publicacao": str(item.get("dataPublicacaoPncp") or "")[:10],
                                    "valor_total_estimado": val_estimado,
                                    "valor_total_homologado": val_homologado,
                                    "valor_auditado": val_ref,
                                    "link_sistema_origem": item.get("linkSistemaOrigem") or pncp_portal_url,
                                    "pncp_portal_url": pncp_portal_url,
                                    "source_sha256": prov["sha256"],
                                    "source_api_url": url,
                                }
                            )
                    except Exception:
                        break
                if rows:
                    break

    if not rows:
        return pl.DataFrame(), provenance_records

    return pl.DataFrame(rows), provenance_records

