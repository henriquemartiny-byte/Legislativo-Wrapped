# 🤖 Guia de Sincronização: Vogon Cívico ↔ Marvin (Chief of Staff)

Este documento define como o agente **Vogon Cívico** se conecta à governança central da holding **Marvin** (`c:\Users\henri\Desktop\agents\marvin`).

---

## 🔗 1. Conexão com os Pilares da Holding
O projeto conduzido pelo **Vogon Cívico** gera valor direto para dois pilares estratégicos do Henrique:

1. **`02-tech-pm` (Tech & Product Management):**
   * Case de referência em **AI Product Architecture & Data Engineering** (arquitetura híbrida onde motores colunares `DuckDB/Polars` executam auditoria determinística em larga escala e LLMs atuam exclusivamente na camada de explicabilidade jurídica e tradução cidadã).
2. **`01-academico-pesquisa` (Acadêmico & Pesquisa):**
   * Laboratório empírico para pesquisa aplicada em **Inteligência Cívica, Transparência Algorítmica, GovTech e Controle Social de Dados Abertos**.

---

## 📋 2. Protocolo de Operação e Fronteiras
* **Autonomia Técnica Local:** O Vogon Cívico tem autonomia total dentro de `c:\Users\henri\Desktop\agents\vogon\` para criar scripts de ingestão, bancos DuckDB, arquivos Parquet, testes estatísticos e aplicações web.
* **Isolamento de Escrita (Sandbox):** O Vogon Cívico **não edita** diretamente arquivos dentro de `c:\Users\henri\Desktop\agents\marvin\` ou no Google Drive (`G:\My Drive`).
* **Registro de Marcos:** Sempre que um marco importante for atingido (ex: *MVP do conector PNCP concluído*, *Primeira trilha de Z-Score validada*, *Dashboard protótipo no ar*), o Vogon Cívico gera um resumo executivo conciso para que o **Marvin** atualize o `00-Raiz/BACKLOG.md` e o `00-Raiz/ROADMAP.md`.

