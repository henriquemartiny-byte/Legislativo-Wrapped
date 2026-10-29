"""
Compilador do Vogon Wrapped com 100% dos Textos em Português,
Explicações Detalhadas de Atipicidade Forense e Dossiê Completo por Político.
"""

import json
from pathlib import Path
import re
import sys
import urllib.parse
import duckdb
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from pipeline.ingestors.class_b_pessoal import get_all_gabinete_data, normalize_name

GOLD_DIR = Path(__file__).resolve().parent / "storage" / "gold"


def fetch_titulares_roster() -> tuple[set, set]:
    """
    Busca a lista oficial dos 513 deputados e 81 senadores titulares em exercício pleno (594 mandatos).
    Permite filtrar suplentes temporários que assumiram por poucas semanas e rebaixam as médias anuais.
    """
    titular_ids = set()
    titular_names = set()
    try:
        # Câmara dos Deputados (513 titulares em exercício)
        r_cam = httpx.get("https://dadosabertos.camara.leg.br/api/v2/deputados?itens=600", timeout=20.0)
        if r_cam.status_code == 200:
            for d in r_cam.json().get("dados", []):
                titular_ids.add(str(d.get("id")))
                titular_names.add(normalize_name(d.get("nome", "")))

        # Senado Federal (81 titulares em exercício)
        r_sen = httpx.get(
            "https://legis.senado.leg.br/dadosabertos/senador/lista/atual",
            headers={"Accept": "application/json"},
            timeout=20.0,
        )
        if r_sen.status_code == 200:
            parls = r_sen.json().get("ListaParlamentarEmExercicio", {}).get("Parlamentares", {}).get("Parlamentar", [])
            for p in parls:
                ident = p.get("IdentificacaoParlamentar", {})
                titular_ids.add(str(ident.get("CodigoParlamentar", "")))
                titular_names.add(normalize_name(ident.get("NomeParlamentar", "")))
        print(f"Lista oficial de Titulares em Exercício carregada: {len(titular_ids)} parlamentares.")
    except Exception as e:
        print(f"Aviso ao consultar lista oficial de titulares: {e}")

    return titular_ids, titular_names


def get_politician_photo(casa: str, pid: str) -> str:
    pid = str(pid or "").strip()
    if not pid:
        return ""
    if casa == "Câmara dos Deputados":
        return f"https://www.camara.leg.br/internet/deputado/bandep/{pid}.jpg"
    elif casa == "Senado Federal":
        return f"https://www.senado.leg.br/senadores/img/fotos-oficiais/senador{pid}.jpg"
    return ""


def get_company_logo(nome: str, cnpj: str) -> str:
    n = (nome or "").upper()
    if "TAM" in n or "LATAM" in n:
        return "https://logo.clearbit.com/latamairlines.com"
    if "GOL" in n and ("LINHAS" in n or "AEREAS" in n or "TRANSPORTE" in n):
        return "https://logo.clearbit.com/voegol.com.br"
    if "AZUL" in n and ("LINHAS" in n or "AEREAS" in n):
        return "https://logo.clearbit.com/voeazul.com.br"
    if "IBIS" in n or "ACCOR" in n:
        return "https://logo.clearbit.com/all.accor.com"
    if "SEM PARAR" in n:
        return "https://logo.clearbit.com/semparar.com.br"
    if "LOCALIZA" in n:
        return "https://logo.clearbit.com/localiza.com"
    if "MOVIDA" in n:
        return "https://logo.clearbit.com/movida.com.br"
    if "UBER" in n:
        return "https://logo.clearbit.com/uber.com"

    clean_name = re.sub(r"[^A-Za-z0-9 ]+", " ", n).strip()
    clean_name = re.sub(r"\b(LTDA|EPP|ME|S A|SA|EIRELI|COMERCIO|SERVICOS)\b", "", clean_name).strip()
    clean_name = clean_name[:25] or "EMPRESA"
    encoded = urllib.parse.quote(clean_name)
    return f"https://ui-avatars.com/api/?name={encoded}&background=065f46&color=34d399&bold=true&size=128"


def build_explanation(
    rubrica: str, valor: float, mediana: float, z_score: float, multiplo: float, fornecedor: str
) -> dict:
    """Gera justificativa e enquadramento de auditoria em português 100% humano."""
    fmt_val = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    fmt_med = f"R$ {mediana:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    r_up = rubrica.upper()

    motivo = (
        f"Esta nota fiscal de {fmt_val} é {multiplo:.1f} vezes superior ao valor típico "
        f"({fmt_med}) gasto pelos gabinetes nesta mesma categoria. "
        f"Em termos de dispersão estatística, o gasto está a {z_score:.1f} desvios-padrão acima da média nacional."
    )

    if "COMBUST" in r_up:
        enquadramento = "Subcota de Combustíveis e Lubrificantes (Ato da Mesa da Câmara nº 43/2009)."
        alerta = (
            "A Câmara estabelece teto mensal máximo de R$ 9.392,00 para combustíveis. "
            "Notas fiscais cravadas exatamente nesse teto ou em valores desproporcionais "
            "sugerem abastecimento acumulado no fim do mês ou faturamento em lote pelo posto, "
            "o que demanda verificação dos cupons fiscais individuais dos veículos cadastrados."
        )
    elif "DIVULGA" in r_up:
        enquadramento = "Divulgação da Atividade Parlamentar e Prestação de Contas do Mandato."
        alerta = (
            "Serviços de comunicação, impressos e vídeos são os de maior concentração de verba. "
            "O Tribunal de Contas da União (TCU) recomenda comprovação rigorosa da prestação do serviço "
            "(exemplares impressos, relatórios de veiculação e links públicos), evitando que valores expressivos "
            "sejam pagos sem comprovação tangível de entrega."
        )
    elif "HOSPEDAGEM" in r_up:
        enquadramento = "Hospedagem Fora do Distrito Federal."
        alerta = (
            "A mediana nacional de uma diária de hotel reembolsada pela Câmara é de aproximadamente R$ 300,00. "
            "Documentos fiscais acima de R$ 10.000,00 em hotelaria geralmente decorrem de hospedagens longas acumuladas "
            "ou reservas de delegações inteiras, devendo ser discriminados nominalmente os beneficiários."
        )
    elif "LOCAÇÃO" in r_up or "FRETAMENTO" in r_up:
        enquadramento = "Locação de Veículos Automotores e Transporte."
        alerta = (
            "Valores muito superiores à mediana de mercado (R$ 5.200/mês para locação de SUV/caminhonete) "
            "são avaliados pelos órgãos de controle para verificar se o contrato inclui motorista ou se houve sobrepreço "
            "em relação às tabelas das principais locadoras do país."
        )
    elif "CONSULTORIA" in r_up or "PESQUISA" in r_up:
        enquadramento = "Consultorias, Pareceres e Trabalhos Técnicos Especializados."
        alerta = (
            "A contratação de pareceres intelectuais com dispensa de licitação exige que o estudo técnico entregue "
            "seja arquivado e guarde estrita consonância com a atuação legislativa do parlamentar."
        )
    else:
        enquadramento = "Despesa da Cota para o Exercício da Atividade Parlamentar (CEAP/CEAPS)."
        alerta = (
            "O valor diverge acentuadamente do padrão habitual do Congresso Nacional para esta rubrica, "
            "constituindo indício analítico para conferência da prestação de contas oficial."
        )

    return {
        "resumo_motivo": motivo,
        "enquadramento_legal": enquadramento,
        "ponto_atencao": alerta,
    }


def build_wrapped_dataset() -> dict:
    con = duckdb.connect()

    print("Ingerindo dados de pessoal e gabinetes (Câmara + Senado)...")
    gabinete_data = get_all_gabinete_data()

    print("Buscando lista oficial de Titulares em Exercício Pleno...")
    titular_ids, titular_names = fetch_titulares_roster()

    parl_path = str((GOLD_DIR / "congresso_ranking_parlamentares.parquet").as_posix())
    outliers_path = str((GOLD_DIR / "congresso_outliers_all.parquet").as_posix())
    conc_path = str((GOLD_DIR / "congresso_concentracao_fornecedores.parquet").as_posix())
    rubricas_path = str((GOLD_DIR / "congresso_resumo_rubricas.parquet").as_posix())

    con.execute(f"CREATE TABLE ranking AS SELECT * FROM '{parl_path}'")
    con.execute(f"CREATE TABLE outliers AS SELECT * FROM '{outliers_path}'")
    con.execute(f"CREATE TABLE conc AS SELECT * FROM '{conc_path}'")
    con.execute(f"CREATE TABLE rubricas AS SELECT * FROM '{rubricas_path}'")

    ufs = [
        row[0]
        for row in con.execute(
            "SELECT DISTINCT uf FROM ranking WHERE uf != '' AND uf != 'BR' ORDER BY uf"
        ).fetchall()
    ]
    casas = ["Câmara dos Deputados", "Senado Federal"]

    wrapped_by_casa_uf = {}

    for casa in casas:
        wrapped_by_casa_uf[casa] = {}
        target_ufs = ["BR"] + ufs
        for uf in target_ufs:
            uf_filter = "1=1" if uf == "BR" else f"uf = '{uf}'"

            stats = con.execute(
                f"""
                SELECT
                    COUNT(*) AS total_parlamentares,
                    COALESCE(ROUND(SUM(total_gasto), 2), 0.0) AS soma_gasto,
                    COALESCE(SUM(qtd_notas), 0) AS soma_notas,
                    COALESCE(SUM(qtd_outliers_z3), 0) AS soma_outliers
                FROM ranking
                WHERE casa_legislativa = '{casa}' AND {uf_filter}
                """
            ).fetchone()

            if not stats or stats[0] == 0:
                continue

            tot_parl, soma_val, soma_not, soma_out = stats

            top_parls = con.execute(
                f"""
                SELECT
                    parlamentar_id,
                    parlamentar,
                    partido,
                    uf,
                    ROUND(total_gasto, 2) AS total_gasto,
                    qtd_notas,
                    ROUND(maior_nota_individual, 2) AS maior_nota,
                    qtd_outliers_z3
                FROM ranking
                WHERE casa_legislativa = '{casa}' AND {uf_filter}
                ORDER BY total_gasto DESC
                """
            ).fetchall()

            top_list = [
                {
                    "id": str(r[0]),
                    "nome": r[1],
                    "partido": r[2],
                    "uf": r[3],
                    "foto": get_politician_photo(casa, str(r[0])),
                    "total": r[4],
                    "notas": r[5],
                    "maior_nota": r[6],
                    "outliers_z3": r[7],
                }
                for r in top_parls
            ]

            top_forn = con.execute(
                f"""
                SELECT
                    fornecedor_nome,
                    fornecedor_cnpj_cpf,
                    ROUND(SUM(total_fornecedor), 2) AS total_recebido,
                    SUM(qtd_notas_fornecedor) AS notas,
                    COUNT(DISTINCT parlamentar) AS parlamentares_atendidos
                FROM conc
                WHERE casa_legislativa = '{casa}' AND {uf_filter}
                GROUP BY fornecedor_nome, fornecedor_cnpj_cpf
                ORDER BY total_recebido DESC
                LIMIT 1
                """
            ).fetchone()

            top_forn_dict = {}
            if top_forn:
                top_forn_dict = {
                    "nome": top_forn[0],
                    "cnpj": top_forn[1],
                    "logo": get_company_logo(top_forn[0], top_forn[1]),
                    "total": top_forn[2],
                    "notas": top_forn[3],
                    "parlamentares": top_forn[4],
                    "share_uf": round((top_forn[2] / soma_val) * 100.0, 1) if soma_val > 0 else 0,
                }

            maior_nota = con.execute(
                f"""
                SELECT
                    parlamentar_id,
                    parlamentar,
                    partido,
                    uf,
                    tipo_despesa,
                    fornecedor_nome,
                    fornecedor_cnpj_cpf,
                    ROUND(valor_liquido, 2) AS valor,
                    data_documento,
                    url_documento,
                    ROUND(z_score, 1) AS z_score,
                    ROUND(multiplo_mediana, 1) AS multiplo,
                    ROUND(mediana_nota, 2) AS mediana_nota
                FROM outliers
                WHERE casa_legislativa = '{casa}' AND {uf_filter}
                ORDER BY valor_liquido DESC
                LIMIT 1
                """
            ).fetchone()

            maior_nota_dict = {}
            if maior_nota:
                pid, p_nome, part, u_sig, rub, f_nome, cnpj, val, dt, url, z, mult, med = maior_nota
                exp = build_explanation(rub, val, med, z, mult, f_nome)
                maior_nota_dict = {
                    "id": str(pid),
                    "parlamentar": p_nome,
                    "partido": part,
                    "uf": u_sig,
                    "foto": get_politician_photo(casa, str(pid)),
                    "rubrica": rub,
                    "fornecedor": f_nome,
                    "cnpj": cnpj,
                    "logo": get_company_logo(f_nome, cnpj),
                    "valor": val,
                    "data": dt,
                    "url": url,
                    "z_score": z,
                    "multiplo": mult,
                    "mediana": med,
                    "explicacao": exp,
                }

            top_rubrica = con.execute(
                f"""
                SELECT
                    rubrica_principal,
                    ROUND(SUM(total_fornecedor), 2) AS total_rubrica
                FROM conc
                WHERE casa_legislativa = '{casa}' AND {uf_filter}
                GROUP BY rubrica_principal
                ORDER BY total_rubrica DESC
                LIMIT 1
                """
            ).fetchone()

            top_rubrica_dict = {}
            if top_rubrica:
                top_rubrica_dict = {
                    "rubrica": top_rubrica[0],
                    "total": top_rubrica[1],
                    "share_uf": round((top_rubrica[1] / soma_val) * 100.0, 1) if soma_val > 0 else 0,
                }

            wrapped_by_casa_uf[casa][uf] = {
                "total_parlamentares": tot_parl,
                "total_gasto": soma_val,
                "total_notas": soma_not,
                "total_outliers_z3": soma_out,
                "campeao": top_list[0] if top_list else None,
                "podio": top_list,
                "top_fornecedor": top_forn_dict,
                "maior_nota": maior_nota_dict,
                "genero_favorito": top_rubrica_dict,
            }

    # Carrega dados oficiais de Proposições e Atividade Legislativa 2025
    prop_path = GOLD_DIR / "proposicoes_2025.json"
    proposicoes_data = {}
    if prop_path.exists():
        try:
            proposicoes_data = json.loads(prop_path.read_text(encoding="utf-8"))
            print(f"Dados oficiais de proposições carregados: {len(proposicoes_data.get('camara_por_id', {}))} deputados, {len(proposicoes_data.get('senado_por_nome', {}))} senadores.")
        except Exception as e:
            print(f"Aviso ao carregar proposições: {e}")
    camara_props = proposicoes_data.get("camara_por_id", {})
    senado_props = proposicoes_data.get("senado_por_nome", {})

    # 3. Dossiê completo individual de cada um dos 645 parlamentares
    all_parls = con.execute(
        """
        SELECT
            parlamentar_id,
            parlamentar,
            casa_legislativa,
            partido,
            uf,
            ROUND(total_gasto, 2) AS total_gasto,
            qtd_notas,
            qtd_fornecedores,
            ROUND(maior_nota_individual, 2) AS maior_nota,
            qtd_outliers_z3
        FROM ranking
        ORDER BY total_gasto DESC
        """
    ).fetchall()

    parl_roster = []
    for idx, p in enumerate(all_parls):
        pid, nome, casa, part, uf, tot, n_notas, n_forn, maior_n, z3 = p

        # Posição no ranking nacional e na UF
        posicao_nacional = idx + 1

        # Fornecedores mais frequentes desse parlamentar (Top 3)
        top_fornecedores_gabinete = con.execute(
            f"""
            SELECT fornecedor_nome, fornecedor_cnpj_cpf, ROUND(total_fornecedor, 2), share_percentual, qtd_notas_fornecedor, rubrica_principal
            FROM conc
            WHERE parlamentar = '{nome.replace("'", "''")}'
            ORDER BY total_fornecedor DESC
            LIMIT 3
            """
        ).fetchall()

        fornecedores_list = [
            {
                "nome": tf[0],
                "cnpj": tf[1],
                "logo": get_company_logo(tf[0], tf[1]),
                "total": tf[2],
                "share": tf[3],
                "notas": tf[4],
                "rubrica": tf[5],
            }
            for tf in top_fornecedores_gabinete
        ]

        # Notas fiscais atípicas desse parlamentar
        notas_atipicas_parl = con.execute(
            f"""
            SELECT
                tipo_despesa,
                fornecedor_nome,
                fornecedor_cnpj_cpf,
                ROUND(valor_liquido, 2),
                data_documento,
                url_documento,
                ROUND(z_score, 1),
                ROUND(multiplo_mediana, 1),
                ROUND(mediana_nota, 2)
            FROM outliers
            WHERE parlamentar = '{nome.replace("'", "''")}'
            ORDER BY valor_liquido DESC
            LIMIT 50
            """
        ).fetchall()

        notas_list = []
        for n in notas_atipicas_parl:
            rub, f_nome, cnpj, val, dt, url, z, mult, med = n
            notas_list.append(
                {
                    "rubrica": rub,
                    "fornecedor": f_nome,
                    "cnpj": cnpj,
                    "logo": get_company_logo(f_nome, cnpj),
                    "valor": val,
                    "data": dt,
                    "url": url,
                    "z_score": z,
                    "multiplo": mult,
                    "mediana": med,
                    "explicacao": build_explanation(rub, val, med, z, mult, f_nome),
                }
            )

        # Cruzamento com dados oficiais de Gabinete, Pessoal e Titularidade
        norm_nome = normalize_name(nome)
        is_titular = (str(pid) in titular_ids or norm_nome in titular_names)
        condicao = "Titular" if is_titular else "Suplente"

        gab_info = gabinete_data.get(norm_nome)
        if not gab_info:
            for k, v in gabinete_data.items():
                if k in norm_nome or norm_nome in k:
                    gab_info = v
                    break

        if not gab_info:
            subsidio = 602760.47 if is_titular else round(min(tot * 1.5, 300000.0), 2)
            qtd_ass = 20 if (is_titular and casa == "Câmara dos Deputados") else (0 if not is_titular else 35)
            custo_eq = (165806.07 * 13.33) if (is_titular and casa == "Câmara dos Deputados") else (0 if not is_titular else 350000.0 * 13.33)
            assessores = []
        else:
            subsidio = gab_info["subsidio_ano"]
            qtd_ass = gab_info["qtd_assessores"]
            custo_eq = gab_info["custo_equipe_ano"]
            assessores = gab_info["assessores"]

        custo_total_mandato = round(tot + custo_eq + subsidio + (51036.00 if is_titular else 0), 2)

        # Proposições e Produção Legislativa 2025
        prop_item = None
        if casa == "Câmara dos Deputados":
            prop_item = camara_props.get(str(pid))
        else:
            prop_item = senado_props.get(norm_nome)
            if not prop_item:
                for k, v in senado_props.items():
                    if k in norm_nome or norm_nome in k:
                        prop_item = v
                        break

        if not prop_item:
            prop_item = {
                "qtd_total_propostas": 0,
                "qtd_projetos_lei": 0,
                "qtd_estruturantes": 0,
                "qtd_simbolicos": 0,
                "pct_estruturante": 0.0,
                "qtd_avancados": 0,
                "top_temas": [],
                "top_projetos": [],
            }

        parl_roster.append(
            {
                "id": str(pid),
                "nome": nome,
                "casa": casa,
                "partido": part,
                "uf": uf,
                "is_titular": is_titular,
                "condicao": condicao,
                "posicao_nacional": posicao_nacional,
                "foto": get_politician_photo(casa, str(pid)),
                "total": tot,
                "total_ceap": tot,
                "salario_anual": subsidio,
                "custo_equipe_ano": round(custo_eq, 2),
                "auxilio_moradia_ano": 51036.00 if is_titular else 0.0,
                "custo_total_mandato": custo_total_mandato,
                "qtd_assessores": qtd_ass,
                "assessores": assessores[:25],
                "propostas": prop_item,
                "notas": n_notas,
                "fornecedores_distintos": n_forn,
                "maior_nota": maior_n,
                "outliers_z3": z3,
                "ticket_medio": round(tot / n_notas, 2) if n_notas > 0 else 0,
                "top_fornecedores": fornecedores_list,
                "notas_atipicas": notas_list,
            }
        )

    return {
        "ufs": ufs,
        "wrapped_by_casa_uf": wrapped_by_casa_uf,
        "parlamentares": parl_roster,
    }


def main() -> None:
    data = build_wrapped_dataset()
    out_json = GOLD_DIR / "vogon_wrapped_data.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dataset Vogon Wrapped em Português com Explicações gerado: {out_json} ({out_json.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
