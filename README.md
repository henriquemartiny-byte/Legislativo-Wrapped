# 🏛️ Legislativo Wrapped & Vogon Cívico — Inteligência Cívica & Auditoria Algorítmica

> **Agente Custodiante:** Vogon Cívico (`GEMINI.md` / `AGENTS.md`)  
> **Arquitetura:** Ingestão Efêmera Classe B + Camada Gold Parquet/DuckDB + Frontend Spotify Design System  
> **Princípio Central:** Auditoria 100% Determinística/Estatística (Polars + DuckDB) com Zero LLM para somatórios. Zero persistência de dados brutos em disco.

---

## 🌟 Produto Entregue: Legislativo Wrapped 2025

Aplicação web completa inspirada no **Spotify Wrapped**, renderizando a retrospectiva de gastos de **todos os 513 Deputados Federais e 81 Senadores da República** com base em **193.825 notas fiscais** e nas folhas de pagamento de gabinetes.

### 🎛️ Principais Recursos da Aplicação:
1. **Dossiê Completo de Gabinete:**
   * **10.344 Secretários Parlamentares** da Câmara mapeados para seus respectivos gabinetes (cargos `SP01` a `SP25`).
   * **3.301 Servidores Comissionados** de Gabinete do Senado mapeados para os 81 senadores.
   * **Subsídio Oficial do Político:** R$ 602.760,47 / ano (fixado por lei + 13º).
2. **Alternador de Avaliação Financeira:**
   * `✈️ Cota Operacional (CEAP)`: Despesas reembolsadas em notas de avião, consultoria, locação de carros/aeronaves, divulgação e combustível.
   * `💼 Custo Total do Gabinete`: Custo integral do mandato (`Cota + Folha de Assessores + Salário + Benefícios`), revelando a despesa real de ~R$ 2,82 Milhões por deputado e ~R$ 4,95 Milhões por senador.
3. **Corte Estatístico de Titulares vs. Suplentes:**
   * **Default:** Audita estritamente os **513 deputados e 81 senadores titulares em exercício pleno (594 mandatos)**, expurgando suplentes temporários que assumiram por semanas e rebaixavam as médias nacionais em ~10%.
   * **Alternador:** Permite ver o universo com suplentes (645 parlamentares).
4. **Filtro Partidário & Ranking Per Capita:**
   * Filtros por sigla partidária (`PL`, `PT`, `UNIÃO`, `PP`, `PSD`, `MDB`, `REPUBLICANOS`, `PSB`, `PSOL`, `NOVO`, etc.).
   * Ranking per capita que elimina a distorção do tamanho da bancada.
5. **Stories Interativos em 4 Slides:**
   * Slide 1: Dossiê Financeiro do Mandato (Custo total e funil dos 4 pilares).
   * Slide 2: A Equipe do Gabinete (Relação nominal de assessores com cargos e folha).
   * Slide 3: Fornecedor Favorito (Empresa privada mais contratada).
   * Slide 4: Auditoria Forense (Notas fiscais com Z-Score > 3 e diagnóstico explicativo).
6. **Buscador Direto no Topo:**
   * Busca em tempo real por nome com fotos oficiais em alta resolução.

---

## 🚀 Como Executar Localmente

### 1. Iniciar o Servidor Web:
```powershell
& "c:\Users\henri\Desktop\agents\vogon\pipeline\.venv\Scripts\python.exe" -m http.server 3333 --directory "c:\Users\henri\Desktop\agents\vogon\web"
```
Acesse no navegador:
👉 **`http://localhost:3333/`** ou **`http://localhost:3333/wrapped.html`**

### 2. Recompilar os Dados e o HTML (Caso Atualize a Base):
```powershell
# 1. Atualizar JSON Gold consolidado
& "c:\Users\henri\Desktop\agents\vogon\pipeline\.venv\Scripts\python.exe" "pipeline/build_wrapped_data.py"

# 2. Compilar HTML único com dados embutidos
& "c:\Users\henri\Desktop\agents\vogon\pipeline\.venv\Scripts\python.exe" "pipeline/build_wrapped_html.py"
```

---

## 🗺️ Estrutura do Repositório

```text
vogon/
├── .gitignore
├── AGENTS.md                        # Diretriz mestra de engenharia, trilhas de auditoria e guardrails
├── GEMINI.md                        # Ponto de entrada de contexto do agente Vogon Cívico
├── PERSONA-VOGON.md                 # Identidade, tom de voz e diretrizes visuais
├── MARVIN-SYNC.md                   # Protocolo de alinhamento com a holding Marvin
├── README.md                        # Este documento
│
├── pipeline/                        # Motor de Dados & Auditoria Determinística
│   ├── .venv/                       # Ambiente virtual isolado (Polars, DuckDB, PyArrow, HTTPX)
│   ├── core/                        # Gerenciador efêmero e roteador de classes de dados
│   ├── ingestors/                   # Conectores Classe B (Câmara, Senado, Pessoal/Secretários, PNCP)
│   ├── auditors/                    # Anomalias determinísticas (Z-Score, concentração, fracionamento)
│   ├── storage/gold/                # Tabelas Parquet ultracompactas e JSON do Wrapped
│   ├── build_wrapped_data.py        # Compilador do dataset enriquecido com dossiê
│   └── build_wrapped_html.py        # Gerador do HTML Spotify Wrapped
│
└── web/                             # Frontend do Legislativo Wrapped
    ├── index.html                   # Redirecionador automático para o Wrapped
    └── wrapped.html                 # Aplicação completa auto-contida (23 MB)
```


