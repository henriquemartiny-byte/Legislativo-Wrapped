"""
Conector Efêmero Classe B — Congresso Nacional:
1. Câmara dos Deputados (CEAP - Todos os 513 Deputados - Com UF e Partido)
2. Senado Federal (CEAPS - Todos os 81 Senadores - Enriquecido com UF, Partido e Foto Oficial)

Ciclo: Baixa em pasta temporária -> Gera Hash SHA-256 -> Processa em Polars -> Auto-deleta 100% dos brutos.
"""

import io
from typing import List, Dict, Any, Tuple
import zipfile
import httpx
import polars as pl

from core.ephemeral_workspace import ephemeral_ingestion_zone, compute_audit_provenance

SENADO_CEAPS_API_URL = "https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/despesas_ceaps/2025"
SENADO_ROSTER_URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"


def fetch_senador_roster(client: httpx.Client) -> Dict[str, Dict[str, str]]:
    """
    Busca a lista atual de senadores para enriquecer os códigos com UF, Partido e Foto.
    """
    roster = {}
    try:
        resp = client.get(SENADO_ROSTER_URL, timeout=15.0)
        if resp.status_code == 200:
            parls = resp.json().get("ListaParlamentarEmExercicio", {}).get("Parlamentares", {}).get("Parlamentar", [])
            for p in parls:
                ident = p.get("IdentificacaoParlamentar", {})
                cod = str(ident.get("CodigoParlamentar", "")).strip()
                nome = str(ident.get("NomeParlamentar", "")).strip().upper()
                partido = str(ident.get("SiglaPartidoParlamentar", "S/P")).strip()
                uf = str(ident.get("UfParlamentar", "BR")).strip().upper()
                foto = str(ident.get("UrlFotoParlamentar", "")).strip()
                info = {"partido": partido, "uf": uf, "foto": foto, "nome": ident.get("NomeParlamentar", "")}
                if cod:
                    roster[cod] = info
                if nome:
                    roster[nome] = info
    except Exception:
        pass
    return roster


def fetch_congresso_cotas_ephemeral(
    ano: int = 2025,
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    provenance_records: List[Dict[str, Any]] = []
    frames: List[pl.DataFrame] = []

    headers = {"Accept": "application/json", "User-Agent": "VogonCivicoAuditEngine/0.1"}

    with ephemeral_ingestion_zone("congresso_cotas") as tmp_dir:
        with httpx.Client(headers=headers, timeout=45.0, follow_redirects=True) as client:
            # 1. CÂMARA DOS DEPUTADOS (CEAP)
            camara_url = f"https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"
            resp_cam = client.get(camara_url)
            if resp_cam.status_code == 200:
                cam_bytes = resp_cam.content
                cam_zip_path = tmp_dir / f"camara_ceap_{ano}.csv.zip"
                cam_zip_path.write_bytes(cam_bytes)
                prov_cam = compute_audit_provenance(cam_bytes, camara_url)
                provenance_records.append(prov_cam)

                with zipfile.ZipFile(io.BytesIO(cam_bytes)) as zf:
                    csv_name = zf.namelist()[0]
                    with zf.open(csv_name) as csv_file:
                        df_raw_cam = pl.read_csv(
                            csv_file,
                            separator=";",
                            infer_schema_length=5000,
                            ignore_errors=True,
                            schema_overrides={
                                "txtCNPJCPF": pl.Utf8,
                                "txtNumero": pl.Utf8,
                                "ideCadastro": pl.Utf8,
                                "vlrLiquido": pl.Float64,
                                "vlrDocumento": pl.Float64,
                                "vlrGlosa": pl.Float64,
                            },
                        )

                df_cam = (
                    df_raw_cam.filter(
                        pl.col("vlrLiquido").is_not_null()
                        & (pl.col("vlrLiquido") > 0)
                        & pl.col("sgUF").is_not_null()
                        & (pl.col("sgUF") != "NA")
                    )
                    .select(
                        pl.lit("Câmara dos Deputados").alias("casa_legislativa"),
                        pl.col("ideCadastro").fill_null(pl.col("nuDeputadoId").cast(pl.Utf8)).alias("parlamentar_id"),
                        pl.col("txNomeParlamentar").str.strip_chars().alias("parlamentar"),
                        pl.col("sgPartido").fill_null("S/P").str.strip_chars().alias("partido"),
                        pl.col("sgUF").fill_null("BR").str.strip_chars().alias("uf"),
                        pl.col("numAno").cast(pl.Int64, strict=False).fill_null(ano).alias("ano"),
                        pl.col("numMes").cast(pl.Int64, strict=False).fill_null(1).alias("mes"),
                        pl.col("txtDescricao")
                        .fill_null("OUTROS")
                        .str.strip_chars()
                        .str.strip_chars_end(".")
                        .str.to_uppercase()
                        .alias("tipo_despesa"),
                        pl.col("txtFornecedor").fill_null("NÃO INFORMADO").str.strip_chars().alias("fornecedor_nome"),
                        pl.col("txtCNPJCPF").fill_null("").str.strip_chars().alias("fornecedor_cnpj_cpf"),
                        pl.col("txtNumero").fill_null("").cast(pl.Utf8).alias("num_documento"),
                        pl.col("ideDocumento").cast(pl.Utf8).fill_null("").alias("cod_documento"),
                        pl.col("datEmissao").fill_null(f"{ano}-01-01").str.slice(0, 10).alias("data_documento"),
                        pl.col("vlrDocumento").fill_null(0.0).cast(pl.Float64).alias("valor_documento"),
                        pl.col("vlrGlosa").fill_null(0.0).cast(pl.Float64).alias("valor_glosa"),
                        pl.col("vlrLiquido").fill_null(0.0).cast(pl.Float64).alias("valor_liquido"),
                        pl.col("urlDocumento").fill_null("").cast(pl.Utf8).alias("url_documento"),
                        pl.lit(prov_cam["sha256"]).alias("source_sha256"),
                        pl.lit(camara_url).alias("source_api_url"),
                    )
                )
                frames.append(df_cam)

            # 2. SENADO FEDERAL (CEAPS)
            senado_roster = fetch_senador_roster(client)
            senado_url = f"https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/despesas_ceaps/{ano}"
            resp_sen = client.get(senado_url)
            if resp_sen.status_code == 200:
                sen_bytes = resp_sen.content
                sen_json_path = tmp_dir / f"senado_ceaps_{ano}.json"
                sen_json_path.write_bytes(sen_bytes)
                prov_sen = compute_audit_provenance(sen_bytes, senado_url)
                provenance_records.append(prov_sen)

                sen_data = resp_sen.json()
                if sen_data:
                    enriched_rows = []
                    for item in sen_data:
                        v_reemb = float(item.get("valorReembolsado") or 0.0)
                        if v_reemb <= 0:
                            continue
                        cod_sen = str(item.get("codSenador") or "").strip()
                        nome_sen = str(item.get("nomeSenador") or "").strip()

                        # Busca UF e Partido no roster oficial
                        info = senado_roster.get(cod_sen) or senado_roster.get(nome_sen.upper()) or {}
                        uf_sen = info.get("uf", "BR")
                        part_sen = info.get("partido", "SENADO")

                        doc_num = str(item.get("documento") or "")
                        tipo_doc = str(item.get("tipoDocumento") or "")
                        tipo_desp = str(item.get("tipoDespesa") or "OUTROS").strip().rstrip(".").upper()

                        enriched_rows.append(
                            {
                                "casa_legislativa": "Senado Federal",
                                "parlamentar_id": cod_sen,
                                "parlamentar": nome_sen.title(),
                                "partido": part_sen,
                                "uf": uf_sen,
                                "ano": int(item.get("ano") or ano),
                                "mes": int(item.get("mes") or 1),
                                "tipo_despesa": tipo_desp,
                                "fornecedor_nome": str(item.get("fornecedor") or "NÃO INFORMADO").strip(),
                                "fornecedor_cnpj_cpf": str(item.get("cpfCnpj") or "").strip(),
                                "num_documento": doc_num,
                                "cod_documento": str(item.get("id") or ""),
                                "data_documento": str(item.get("data") or f"{ano}-01-01")[:10],
                                "valor_documento": v_reemb,
                                "valor_glosa": 0.0,
                                "valor_liquido": v_reemb,
                                "url_documento": f"https://www6g.senado.leg.br/transparencia/sen/{cod_sen}",
                                "source_sha256": prov_sen["sha256"],
                                "source_api_url": senado_url,
                            }
                        )

                    if enriched_rows:
                        frames.append(pl.DataFrame(enriched_rows))

    if not frames:
        return pl.DataFrame(), provenance_records

    return pl.concat(frames, how="vertical_relaxed"), provenance_records
