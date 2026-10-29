"""
Tradutor de "Orçamentês" e Enquadramento Legal Cidadão (Última Milha).
Respeita estritamente o Guardrail Forense (Padrão TCU/CGU).
"""

from typing import Dict

RUBRICA_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR": {
        "humano": "Divulgação de Mandato, Redes Sociais e Produção Gráfica",
        "explicacao": "Reembolso de serviços de comunicação, vídeos, assessoria de imprensa, impulsionamento e panfletos do parlamentar.",
        "risco_tipico": "Alta concentração em único fornecedor ou notas fiscais de valor fixo mensal próximo ao teto.",
    },
    "LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES": {
        "humano": "Aluguel de Carros, Caminhonetes e Vans para o Gabinete",
        "explicacao": "Custeio mensal de veículos alugados pelo parlamentar e sua equipe em Brasília ou na base eleitoral.",
        "risco_tipico": "Valor unitário de locação mensal acima da mediana praticada para veículos equivalentes.",
    },
    "COMBUSTÍVEIS E LUBRIFICANTES": {
        "humano": "Abastecimento de Combustível (Gasolina, Etanol e Diesel)",
        "explicacao": "Notas fiscais de postos de combustível utilizadas pelos veículos do gabinete parlamentar.",
        "risco_tipico": "Notas fiscais em volume mensal elevado (múltiplos desvios-padrão acima da mediana) ou concentradas em único posto.",
    },
    "MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR": {
        "humano": "Aluguel de Escritório Político no Estado, Energia, Internet e Informática",
        "explicacao": "Despesas fixas para manter a base física de atendimento do parlamentar em seu estado de origem.",
        "risco_tipico": "Locações de imóveis ou equipamentos de TI com valores acima do intervalo interquartil.",
    },
    "CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS": {
        "humano": "Contratação de Consultorias Jurídicas, Técnicas e Pesquisas",
        "explicacao": "Serviços intelectuais especializados contratados diretamente pelo gabinete parlamentar.",
        "risco_tipico": "Baixa tangibilidade física do entregável e alta concentração em único CNPJ.",
    },
    "PASSAGENS AÉREAS": {
        "humano": "Emissão de Bilhetes Aéreos Nacionais",
        "explicacao": "Deslocamentos aéreos do parlamentar e assessores autorizados entre o estado de origem e Brasília.",
        "risco_tipico": "Emissões de última hora com tarifa cheia muy acima da mediana da rota.",
    },
    "TELEFONIA": {
        "humano": "Contas de Telefonia Móvel e Fixa",
        "explicacao": "Comunicação telefônica institucional do parlamentar.",
        "risco_tipico": "Baixo risco unitário.",
    },
    "FORNECIMENTO DE ALIMENTAÇÃO DO PARLAMENTAR": {
        "humano": "Refeições e Alimentação do Parlamentar em Viagem",
        "explicacao": "Reembolso de notas fiscais de restaurantes e lanchonetes (vedado o pagamento para terceiros).",
        "risco_tipico": "Refeições individuais com valor múltiplas vezes superior à mediana de alimentação.",
    },
    "HOSPEDAGEM ,EXCETO DO PARLAMENTAR NO DISTRITO FEDERAL": {
        "humano": "Diárias de Hotéis em Viagens Oficiais (Fora de Brasília)",
        "explicacao": "Hospedagem do parlamentar em missões ou deslocamentos na base eleitoral.",
        "risco_tipico": "Diárias hoteleiras em patamar superior ao intervalo interquartil.",
    },
}


def translate_rubrica(tipo_despesa: str) -> Dict[str, str]:
    key = (tipo_despesa or "").strip().rstrip(".").upper()
    if key in RUBRICA_TRANSLATIONS:
        return RUBRICA_TRANSLATIONS[key]
    for k, v in RUBRICA_TRANSLATIONS.items():
        if k in key or key in k:
            return v
    return {
        "humano": tipo_despesa.title() if tipo_despesa else "Despesa Pública Geral",
        "explicacao": "Despesa custeada com recursos públicos sujeita à prestação de contas e transparência ativa.",
        "risco_tipico": "Monitoramento estatístico de preço unitário (Z-Score) e concentração de fornecedor.",
    }

