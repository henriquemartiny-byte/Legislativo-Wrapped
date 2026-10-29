"""
Conector Classe A (Remote Pushdown via Google BigQuery / basedosdados).

Gera queries SQL parametrizadas para execução remota sem download da base bruta:
1. Receita Federal (CNPJ + Quadro Societário QSA - +60M empresas)
2. SICONFI / Tesouro Nacional (Execução Orçamentária Municipal)
3. Portal da Transparência / CGU (Emendas Parlamentares & CEIS/CNEP)
4. TSE (Doações e Fornecedores de Campanha Eleitoral)
"""

from typing import List


def build_qsa_pushdown_query(target_cnpjs: List[str]) -> str:
    """
    Constrói query pushdown para o BigQuery (`basedosdados.br_me_cnpj`)
    filtrando estritamente pelos CNPJs vencedores de licitações ou recebedores da Cota Parlamentar.
    """
    cleaned = [c.replace(".", "").replace("/", "").replace("-", "").strip() for c in target_cnpjs if c]
    cleaned = [c for c in cleaned if len(c) == 14][:500]
    in_clause = ", ".join(f"'{c}'" for c in cleaned) or "''"

    return f"""
    SELECT
        e.cnpj_basico,
        est.cnpj,
        e.razao_social,
        e.natureza_juridica,
        e.capital_social,
        est.data_inicio_atividade,
        est.cnae_fiscal_principal,
        est.sigla_uf,
        est.id_municipio,
        s.nome_socio,
        s.documento_socio,
        s.qualificacao_socio
    FROM `basedosdados.br_me_cnpj.estabelecimentos` est
    JOIN `basedosdados.br_me_cnpj.empresas` e
      ON est.cnpj_basico = e.cnpj_basico
    LEFT JOIN `basedosdados.br_me_cnpj.socios` s
      ON est.cnpj_basico = s.cnpj_basico
    WHERE est.cnpj IN ({in_clause})
    """


def build_tse_supplier_cross_query(target_cnpjs: List[str], ano_eleicao: int = 2022) -> str:
    """
    Cruza remotamente se os fornecedores contratados na Cota Parlamentar (CEAP/CEAPS)
    foram doadores ou fornecedores de campanha eleitoral no TSE.
    """
    cleaned = [c.replace(".", "").replace("/", "").replace("-", "").strip() for c in target_cnpjs if c]
    cleaned = [c for c in cleaned if len(c) in (11, 14)][:500]
    in_clause = ", ".join(f"'{c}'" for c in cleaned) or "''"

    return f"""
    SELECT
        ano,
        sigla_uf,
        id_candidato_bd,
        cpf_cnpj_fornecedor,
        nome_fornecedor,
        SUM(valor_despesa) AS total_recebido_campanha
    FROM `basedosdados.br_tse_eleicoes.despesas_candidato`
    WHERE ano = {ano_eleicao}
      AND cpf_cnpj_fornecedor IN ({in_clause})
    GROUP BY 1, 2, 3, 4, 5
    ORDER BY total_recebido_campanha DESC
    """

