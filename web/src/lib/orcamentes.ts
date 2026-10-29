/**
 * Dicionário de Tradução de "Orçamentês" e Enquadramento Legal (Vogon Cívico)
 * Converte rubricas contábeis (SICONFI), categorias da Cota Parlamentar (CEAP/CEAPS)
 * e incisos da Lei nº 14.133/2021 para linguagem cidadã acessível, mantendo rigor forense.
 */

export interface RubricaTranslation {
  codigoOuChave: string;
  tituloHumano: string;
  explicacaoCidada: string;
  baseLegal: string;
  focoAuditoria: string;
}

export const ORCAMENTES_DICTIONARY: Record<string, RubricaTranslation> = {
  "339030": {
    codigoOuChave: "Elemento 339030",
    tituloHumano: "Material de Consumo do Dia a Dia",
    explicacaoCidada:
      "Compras de itens que se esgotam com o uso: papel sulfite, combustível, medicamentos básicos, merenda escolar e produtos de limpeza.",
    baseLegal: "Portaria Interministerial STN/SOF nº 163/2001",
    focoAuditoria:
      "Fracionamento de despesa em pequenas dispensas (Art. 75, II) e sobrepreço unitário (Z-Score) em itens padronizados CATMAT.",
  },
  "339039": {
    codigoOuChave: "Elemento 339039",
    tituloHumano: "Serviços Terceirizados (Pessoa Jurídica)",
    explicacaoCidada:
      "Contratação de empresas para serviços contínuos ou pontuais: limpeza, vigilância, licenças de software, manutenção predial e eventos.",
    baseLegal: "Lei nº 14.133/2021 • Art. 6º e Art. 75",
    focoAuditoria:
      "Aditivos contratuais sucessivos, especificações restritivas e sobreposição societária (QSA) entre concorrentes.",
  },
  "449052": {
    codigoOuChave: "Elemento 449052",
    tituloHumano: "Compra de Máquinas, Veículos e Equipamentos Permanentes",
    explicacaoCidada:
      "Bens duráveis que entram para o patrimônio público: ambulâncias, computadores, tratores, mobiliário escolar e aparelhos hospitalares.",
    baseLegal: "Lei nº 4.320/1964 • Despesa de Capital (Investimento)",
    focoAuditoria:
      "Comparação de preço unitário com a mediana nacional do PNCP para o mesmo modelo/especificação técnica.",
  },
  "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR": {
    codigoOuChave: "CEAP • Divulgação Parlamentar",
    tituloHumano: "Divulgação de Mandato, Redes Sociais e Produção Gráfica",
    explicacaoCidada:
      "Reembolso de notas fiscais de agências de comunicação, vídeos, assessoria de imprensa e informativos de prestação de contas do mandato.",
    baseLegal: "Ato da Mesa da Câmara nº 43/2009",
    focoAuditoria:
      "Índice de concentração em fornecedor único (HHI), notas fiscais sequenciais e maturidade do CNPJ na Receita Federal.",
  },
  "LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES": {
    codigoOuChave: "CEAP • Locação de Veículos",
    tituloHumano: "Aluguel de Carros, Caminhonetes e Vans para o Gabinete",
    explicacaoCidada:
      "Reembolso mensal pelo aluguel de veículos utilizados pelo parlamentar e equipe em Brasília ou na base eleitoral.",
    baseLegal: "Ato da Mesa da Câmara nº 43/2009",
    focoAuditoria:
      "Desvio interquartil (IQR) do valor mensal por veículo frente à mediana da Câmara/Senado.",
  },
  "COMBUSTÍVEIS E LUBRIFICANTES": {
    codigoOuChave: "CEAP • Combustíveis",
    tituloHumano: "Abastecimento de Combustível (Gasolina, Etanol e Diesel)",
    explicacaoCidada:
      "Notas fiscais de postos de combustíveis pagas com a cota parlamentar para deslocamento em serviço.",
    baseLegal: "Ato da Mesa da Câmara nº 43/2009",
    focoAuditoria:
      "Z-Score de volume financeiro em uma única nota fiscal ou acúmulo mensal fisicamente atípico.",
  },
};

