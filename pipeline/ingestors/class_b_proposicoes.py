"""
Ingestor Efêmero de Proposições e Atividade Legislativa 2025 (Câmara dos Deputados + Senado Federal).

Princípio 2 do Vogon:
- Baixa dados brutos de 2025 em diretório temporário (tempfile);
- Processa agregação temática, autoria e classificação (estruturante vs simbólico) em DuckDB/Polars;
- Salva apenas a camada agregada Gold (JSON / Parquet);
- Deleta 100% dos arquivos temporários brutos ao final.
"""

import json
import logging
import os
import re
import tempfile
import urllib.request
from typing import Any

import duckdb
import polars as pl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("class_b_proposicoes")


def normalize_str(s: str) -> str:
    if not s:
        return ""
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII").strip().upper()


def ingest_proposicoes_2025() -> dict[str, Any]:
    """
    Ingesta e processa a produção legislativa de 2025 para todos os 513 deputados e 81 senadores.
    Retorna dicionário indexado por id/nome do parlamentar com métricas e principais projetos.
    """
    results: dict[str, Any] = {
        "camara_por_id": {},
        "senado_por_nome": {},
        "estatisticas_gerais": {},
    }

    headers = {"User-Agent": "LegislativoWrapped/1.0", "Accept": "application/json"}

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Download Câmara bulk datasets
        f_prop = os.path.join(tmpdir, "proposicoes.csv")
        f_autores = os.path.join(tmpdir, "autores.csv")
        f_temas = os.path.join(tmpdir, "temas.csv")

        logger.info("Baixando proposicoesAutores-2025.csv...")
        urllib.request.urlretrieve(
            "https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-2025.csv",
            f_autores,
        )

        logger.info("Baixando proposicoes-2025.csv...")
        urllib.request.urlretrieve(
            "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-2025.csv",
            f_prop,
        )

        logger.info("Baixando proposicoesTemas-2025.csv...")
        urllib.request.urlretrieve(
            "https://dadosabertos.camara.leg.br/arquivos/proposicoesTemas/csv/proposicoesTemas-2025.csv",
            f_temas,
        )

        con = duckdb.connect(":memory:")

        f_autores_clean = f_autores.replace("\\", "/")
        f_prop_clean = f_prop.replace("\\", "/")
        f_temas_clean = f_temas.replace("\\", "/")

        logger.info("Processando proposições da Câmara com DuckDB...")

        # Tabela base de proposições filtradas com autoria principal
        con.execute(
            f"""
            CREATE TABLE camara_base AS
            SELECT 
                a.idDeputadoAutor AS id_deputado,
                a.nomeAutor AS nome,
                a.siglaPartidoAutor AS partido,
                a.siglaUfAutor AS uf,
                p.id AS id_proposicao,
                p.siglaTipo AS tipo,
                p.numero,
                p.ano,
                p.ementa,
                p.dataApresentacao,
                p.ultimoStatus_descricaoSituacao AS situacao,
                CASE 
                    WHEN LOWER(p.ementa) LIKE '%dia nacional%' 
                      OR LOWER(p.ementa) LIKE '%institui o dia%'
                      OR LOWER(p.ementa) LIKE '%denomina%'
                      OR LOWER(p.ementa) LIKE '%patrono%'
                      OR LOWER(p.ementa) LIKE '%patrona%'
                      OR LOWER(p.ementa) LIKE '%capital nacional%'
                      OR LOWER(p.ementa) LIKE '%homenageia%'
                    THEN 'SIMBÓLICO'
                    ELSE 'ESTRUTURANTE'
                END AS categoria,
                CASE
                    WHEN p.siglaTipo IN ('PL', 'PLP', 'PEC', 'PDL', 'MPV') THEN 1
                    ELSE 0
                END AS is_lei
            FROM read_csv('{f_autores_clean}', sep=';', header=true, all_varchar=true) a
            JOIN read_csv('{f_prop_clean}', sep=';', header=true, all_varchar=true) p
              ON a.idProposicao = p.id
            WHERE a.idDeputadoAutor IS NOT NULL 
              AND a.idDeputadoAutor != ''
              AND a.proponente = '1'
              AND a.ordemAssinatura = '1'
            """
        )

        # Temas associados
        con.execute(
            f"""
            CREATE TABLE camara_temas_agg AS
            SELECT 
                b.id_deputado,
                t.tema,
                COUNT(*) AS qtd_tema
            FROM camara_base b
            JOIN read_csv('{f_temas_clean}', sep=';', header=true, all_varchar=true) t
              ON 'https://dadosabertos.camara.leg.br/api/v2/proposicoes/' || b.id_proposicao = t.uriProposicao
            WHERE t.tema IS NOT NULL AND t.tema != ''
            GROUP BY b.id_deputado, t.tema
            """
        )

        # Totais por deputado
        df_dep_stats = con.sql(
            """
            SELECT 
                id_deputado,
                COUNT(*) AS qtd_total,
                SUM(is_lei) AS qtd_leis,
                SUM(CASE WHEN is_lei = 1 AND categoria = 'ESTRUTURANTE' THEN 1 ELSE 0 END) AS qtd_estruturantes,
                SUM(CASE WHEN is_lei = 1 AND categoria = 'SIMBÓLICO' THEN 1 ELSE 0 END) AS qtd_simbolicos,
                SUM(CASE WHEN situacao LIKE '%Aprovad%' OR situacao LIKE '%Senado%' OR situacao LIKE '%Norma%' THEN 1 ELSE 0 END) AS qtd_avancados
            FROM camara_base
            GROUP BY id_deputado
            """
        ).pl()

        # Principais projetos por deputado (Top 5 leis)
        df_top_projetos = con.sql(
            """
            WITH ranked AS (
                SELECT 
                    id_deputado,
                    id_proposicao,
                    tipo,
                    numero,
                    ano,
                    ementa,
                    categoria,
                    dataApresentacao,
                    situacao,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_deputado 
                        ORDER BY is_lei DESC, (categoria = 'ESTRUTURANTE') DESC, dataApresentacao DESC
                    ) AS rn
                FROM camara_base
                WHERE is_lei = 1
            )
            SELECT * FROM ranked WHERE rn <= 5
            """
        ).pl()

        # Mapear top temas por deputado
        df_temas = con.sql(
            """
            WITH ranked_temas AS (
                SELECT 
                    id_deputado,
                    tema,
                    qtd_tema,
                    ROW_NUMBER() OVER (PARTITION BY id_deputado ORDER BY qtd_tema DESC) AS rn
                FROM camara_temas_agg
            )
            SELECT * FROM ranked_temas WHERE rn <= 6
            """
        ).pl()

        # Agrupar temas por id_deputado em dicionário
        temas_map: dict[str, list[dict[str, Any]]] = {}
        for row in df_temas.iter_rows(named=True):
            dep_id = str(row["id_deputado"])
            temas_map.setdefault(dep_id, []).append({
                "tema": str(row["tema"] or ""),
                "qtd": int(row["qtd_tema"] or 0)
            })

        # Agrupar projetos por id_deputado em dicionário
        projetos_map: dict[str, list[dict[str, Any]]] = {}
        for row in df_top_projetos.iter_rows(named=True):
            dep_id = str(row["id_deputado"])
            id_prop = str(row.get("id_proposicao") or "")
            url = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_prop}" if id_prop else ""
            projetos_map.setdefault(dep_id, []).append({
                "id_proposicao": id_prop,
                "codigo": f"{row['tipo']} {row['numero']}/{row['ano']}",
                "tipo": str(row["tipo"] or ""),
                "ementa": str(row["ementa"] or ""),
                "categoria": str(row["categoria"] or "ESTRUTURANTE"),
                "situacao": str(row["situacao"] or "Em tramitação"),
                "url": url,
            })

        # Consolidar dados da Câmara
        for row in df_dep_stats.iter_rows(named=True):
            dep_id = str(row["id_deputado"])
            total_leis = int(row["qtd_leis"] or 0)
            estrut = int(row["qtd_estruturantes"] or 0)
            pct_estrut = round((float(estrut) / float(total_leis) * 100), 1) if total_leis > 0 else 0.0

            results["camara_por_id"][dep_id] = {
                "qtd_total_propostas": int(row["qtd_total"] or 0),
                "qtd_projetos_lei": total_leis,
                "qtd_estruturantes": estrut,
                "qtd_simbolicos": int(row["qtd_simbolicos"] or 0),
                "pct_estruturante": pct_estrut,
                "qtd_avancados": int(row["qtd_avancados"] or 0),
                "top_temas": temas_map.get(dep_id, []),
                "top_projetos": projetos_map.get(dep_id, []),
            }

        logger.info(f"Câmara processada com sucesso: {len(results['camara_por_id'])} deputados mapeados.")

    # 2. Ingestão Senado Federal via API
    logger.info("Buscando matérias de 2025 do Senado Federal...")
    try:
        url_senado = "https://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?ano=2025"
        req = urllib.request.Request(url_senado, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            senado_data = json.loads(r.read().decode())
            materias = senado_data.get("PesquisaBasicaMateria", {}).get("Materias", {}).get("Materia", [])

            # Agrupar matérias por senador
            senadores_propostas: dict[str, list[dict[str, Any]]] = {}
            for m in materias:
                autor_str = m.get("Autor", "")
                if "Senador" in autor_str:
                    # Ex: 'Senador Alessandro Vieira (MDB/SE)' -> 'ALESSANDRO VIEIRA'
                    clean_name = re.sub(r"Senador[a]?\s+", "", autor_str, flags=re.I)
                    clean_name = re.sub(r"\s*\(.*?\)", "", clean_name).strip()
                    norm_name = normalize_str(clean_name)
                    
                    sigla = m.get("Sigla", "")
                    ementa = m.get("Ementa", "")
                    numero = m.get("Numero", "")
                    ano = m.get("Ano", "2025")

                    is_lei = 1 if sigla in ["PL", "PEC", "PLP", "PDL", "PRS"] else 0
                    categoria = "SIMBÓLICO" if any(w in ementa.lower() for w in ["dia nacional", "institui o dia", "denomina", "patrono", "homenageia"]) else "ESTRUTURANTE"

                    codigo_mat = m.get("Codigo", "")
                    url_sen = m.get("UrlDetalheMateria") or f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo_mat}"
                    senadores_propostas.setdefault(norm_name, []).append({
                        "id_proposicao": codigo_mat,
                        "codigo": f"{sigla} {int(numero) if numero.isdigit() else numero}/{ano}",
                        "tipo": sigla,
                        "ementa": ementa,
                        "categoria": categoria,
                        "is_lei": is_lei,
                        "situacao": "Em tramitação no Senado",
                        "url": url_sen,
                    })

            for norm_name, items in senadores_propostas.items():
                total = len(items)
                leis = [it for it in items if it["is_lei"] == 1]
                estrut = [it for it in leis if it["categoria"] == "ESTRUTURANTE"]
                simb = [it for it in leis if it["categoria"] == "SIMBÓLICO"]
                pct_estrut = round((len(estrut) / len(leis) * 100), 1) if leis else 0.0

                results["senado_por_nome"][norm_name] = {
                    "qtd_total_propostas": total,
                    "qtd_projetos_lei": len(leis),
                    "qtd_estruturantes": len(estrut),
                    "qtd_simbolicos": len(simb),
                    "pct_estruturante": pct_estrut,
                    "qtd_avancados": 0,
                    "top_temas": [],
                    "top_projetos": leis[:5],
                }

            logger.info(f"Senado processado com sucesso: {len(results['senado_por_nome'])} senadores mapeados.")

    except Exception as e:
        logger.error(f"Erro ao processar dados do Senado: {e}")

    # Salva snapshot Gold leve
    out_gold = os.path.join(
        os.path.dirname(__file__), "..", "storage", "gold", "proposicoes_2025.json"
    )
    os.makedirs(os.path.dirname(out_gold), exist_ok=True)
    with open(out_gold, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Dados Gold de proposições salvos em: {out_gold}")

    return results


if __name__ == "__main__":
    ingest_proposicoes_2025()

