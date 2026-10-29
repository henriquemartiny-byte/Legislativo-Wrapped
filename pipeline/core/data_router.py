"""
Catálogo e Roteador Automático por Natureza do Dado (Classes A, B e C).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class DataClass(str, Enum):
    CLASS_A_REMOTE_PUSHDOWN = "class_a_remote_pushdown"   # BigQuery (basedosdados) - Zero download bruto
    CLASS_B_EPHEMERAL_STREAM = "class_b_ephemeral_stream" # APIs REST (PNCP/CGU) - Baixa em /tmp, processa e deleta
    CLASS_C_GOLD_SNAPSHOT = "class_c_gold_snapshot"       # MotherDuck / Gold Parquet local leve (< 20 MB)


@dataclass(frozen=True)
class DataSourcePolicy:
    name: str
    data_class: DataClass
    engine: str
    persist_raw: bool
    description: str


DATA_SOURCE_POLICIES: Dict[str, DataSourcePolicy] = {
    "receita_qsa": DataSourcePolicy(
        name="Receita Federal (CNPJ + Quadro Societário)",
        data_class=DataClass.CLASS_A_REMOTE_PUSHDOWN,
        engine="Google BigQuery (basedosdados.br_me_cnpj)",
        persist_raw=False,
        description="Consulta remota filtrada apenas pelos CNPJs que venceram licitações.",
    ),
    "siconfi": DataSourcePolicy(
        name="SICONFI / Tesouro Nacional",
        data_class=DataClass.CLASS_A_REMOTE_PUSHDOWN,
        engine="Google BigQuery (basedosdados.br_me_siconfi) + API STN",
        persist_raw=False,
        description="Balanços orçamentários municipais/estaduais (Orçado, Empenhado, Liquidado, Pago).",
    ),
    "ibge": DataSourcePolicy(
        name="IBGE (População & PIB Municipal)",
        data_class=DataClass.CLASS_A_REMOTE_PUSHDOWN,
        engine="Google BigQuery (basedosdados.br_ibge_populacao / pib)",
        persist_raw=False,
        description="Denominadores demográficos e econômicos para cálculo de indicadores per capita.",
    ),
    "pncp": DataSourcePolicy(
        name="Portal Nacional de Contratações Públicas (Lei 14.133)",
        data_class=DataClass.CLASS_B_EPHEMERAL_STREAM,
        engine="Python httpx + Polars + DuckDB (via ephemeral_ingestion_zone)",
        persist_raw=False,
        description="Baixa lotes em /tmp, grava hash SHA-256, extrai itens/anomalias e apaga o bruto.",
    ),
    "cgu_sancoes": DataSourcePolicy(
        name="CGU (CEIS / CNEP - Empresas Inidôneas e Punidas)",
        data_class=DataClass.CLASS_B_EPHEMERAL_STREAM,
        engine="DuckDB + Polars (Efêmero)",
        persist_raw=False,
        description="Cruzamento em memória contra CNPJs contratados e descarte imediato do arquivo bruto.",
    ),
    "camara_cota": DataSourcePolicy(
        name="Câmara dos Deputados (CEAP - Cota Parlamentar & Notas Fiscais)",
        data_class=DataClass.CLASS_B_EPHEMERAL_STREAM,
        engine="Python httpx + Polars + DuckDB (API Dados Abertos Câmara + BigQuery)",
        persist_raw=False,
        description="Reembolsos de deputados federais nível nota fiscal (CNPJ, rubrica, valor e link PDF) via ingestão efêmera.",
    ),
    "senado_cota": DataSourcePolicy(
        name="Senado Federal (CEAPS - Cota Parlamentar dos Senadores)",
        data_class=DataClass.CLASS_B_EPHEMERAL_STREAM,
        engine="Python httpx + Polars + DuckDB (API Dados Abertos Senado)",
        persist_raw=False,
        description="Despesas e reembolsos de senadores auditados em memória com descarte do bruto.",
    ),
    "cgu_emendas_cpgf": DataSourcePolicy(
        name="Portal da Transparência CGU (Emendas Parlamentares & Cartão Corporativo CPGF)",
        data_class=DataClass.CLASS_A_REMOTE_PUSHDOWN,
        engine="Google BigQuery (basedosdados.br_cgu_*) + API Portal da Transparência",
        persist_raw=False,
        description="Rastreio de emendas parlamentares (autor -> município favorecido) e gastos de cartão corporativo.",
    ),
    "tse_eleicoes": DataSourcePolicy(
        name="TSE (Doações e Despesas de Campanha Eleitoral)",
        data_class=DataClass.CLASS_A_REMOTE_PUSHDOWN,
        engine="Google BigQuery (basedosdados.br_tse_eleicoes)",
        persist_raw=False,
        description="Cruzamento remoto entre fornecedores de gabinete/licitações e doadores ou fornecedores de campanha.",
    ),
    "dashboard_gold": DataSourcePolicy(
        name="Camada Gold (Cubos Analíticos & Alertas para Web)",
        data_class=DataClass.CLASS_C_GOLD_SNAPSHOT,
        engine="MotherDuck (Cloud) + pipeline/storage/gold/*.parquet",
        persist_raw=True,
        description="Única camada mantida pronta para consumo sub-segundo pelos dashboards Next.js.",
    ),
}

