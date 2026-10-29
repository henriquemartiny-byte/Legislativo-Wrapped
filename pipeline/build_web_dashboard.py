"""
Gera o Dashboard Exploratório Standalone (`web/mvp_dashboard.html`) injetando
diretamente os dados reais auditados em `pipeline/storage/gold/mvp_lean_ui.json`
sem gastar tokens de LLM para serializar JSON.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEAN_JSON = ROOT / "pipeline" / "storage" / "gold" / "mvp_lean_ui.json"
OUT_HTML = ROOT / "web" / "mvp_dashboard.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Vogon Cívico • Painel Exploratório de Auditoria (MVP Real)</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased p-6">
  <div class="max-w-7xl mx-auto space-y-6">
    <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 text-xs font-bold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">CAMADA GOLD • 100% DETERMINÍSTICO</span>
          <span class="px-2.5 py-0.5 text-xs font-mono rounded bg-slate-800 text-slate-300">Polars 2.1 + DuckDB 2.0</span>
        </div>
        <h1 class="text-2xl font-bold mt-1">🏛️ Vogon Cívico — Explorador de Atipicidades Públicas (MVP)</h1>
        <p class="text-sm text-slate-400">Auditoria real sobre 193.825 Notas Fiscais (Câmara + Senado 2025) e 147 Dispensas do PNCP (Lei 14.133/2021) • Rastro bruto no disco: 0 bytes</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button onclick="switchTab('outliers')" id="tab-outliers" class="px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-600 text-white">1. Outliers Parlamentares (Z-Score)</button>
        <button onclick="switchTab('conc')" id="tab-conc" class="px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300">2. Concentração de Fornecedor (HHI)</button>
        <button onclick="switchTab('pncp')" id="tab-pncp" class="px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300">3. PNCP • Fracionamento (Art. 75)</button>
        <button onclick="switchTab('rubricas')" id="tab-rubricas" class="px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300">4. Tradutor de Orçamentês</button>
      </div>
    </header>

    <section class="grid grid-cols-2 md:grid-cols-4 gap-4" id="kpi-cards"></section>

    <section class="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 id="section-title" class="text-base font-semibold text-white"></h2>
        <input id="search-input" oninput="renderCurrentTab()" type="text" placeholder="Filtrar por parlamentar, órgão, CNPJ, UF ou rubrica..." class="px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 w-80" />
      </div>
      <div id="table-container" class="overflow-x-auto"></div>
    </section>

    <footer class="text-xs text-slate-500 border-t border-slate-900 pt-4 flex flex-wrap justify-between gap-2">
      <span>Guardrail Forense (Padrão TCU/CGU): Outliers estatísticos (Z-Score &ge; 3) constituem indícios analíticos para verificação documental, não sentença judicial.</span>
      <span id="prov-footer" class="font-mono"></span>
    </footer>
  </div>

  <script>
    const GOLD = __GOLD_PAYLOAD__;
    let currentTab = 'outliers';

    const fmtBRL = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    function initKPIs() {
      const k = GOLD.kpis;
      const items = [
        { label: "Notas Fiscais Auditadas (Congresso)", val: k.ceap_notas_auditadas.toLocaleString('pt-BR'), sub: `${k.ceap_parlamentares_amostra} parlamentares • ${k.ceap_fornecedores_distintos.toLocaleString('pt-BR')} fornecedores` },
        { label: "Volume Financeiro Auditado", val: fmtBRL(k.ceap_valor_total_auditado + k.pncp_valor_total_auditado), sub: `Congresso: ${fmtBRL(k.ceap_valor_total_auditado)} | PNCP: ${fmtBRL(k.pncp_valor_total_auditado)}` },
        { label: "Outliers Severos (Z-Score >= 3)", val: k.ceap_atipicidades_z3.toLocaleString('pt-BR') + " notas", sub: "Acima de 3 desvios-padrão da média da rubrica" },
        { label: "Alertas PNCP (Lei 14.133 • Art. 75)", val: `${k.pncp_alertas_art75} / ${k.pncp_dispensas_auditadas}`, sub: "Acúmulo de dispensas ou limiar de teto (90-100%)" }
      ];
      document.getElementById('kpi-cards').innerHTML = items.map(i => `
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div class="text-xs text-slate-400">${i.label}</div>
          <div class="text-lg font-bold text-white mt-1">${i.val}</div>
          <div class="text-xs text-slate-400 mt-1">${i.sub}</div>
        </div>
      `).join('');
      document.getElementById('prov-footer').textContent = `SHA-256 Câmara: ${GOLD.prov[0].sha256.slice(0,16)}... | Senado: ${GOLD.prov[1].sha256.slice(0,16)}...`;
    }

    function switchTab(tab) {
      currentTab = tab;
      ['outliers', 'conc', 'pncp', 'rubricas'].forEach(t => {
        document.getElementById('tab-' + t).className = (t === tab)
          ? "px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-600 text-white"
          : "px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700";
      });
      renderCurrentTab();
    }

    function renderCurrentTab() {
      const q = (document.getElementById('search-input').value || '').toLowerCase();
      const box = document.getElementById('table-container');
      const title = document.getElementById('section-title');

      if (currentTab === 'outliers') {
        title.textContent = "Trilha 2 • Maiores Desvios Estatísticos por Nota Fiscal (Câmara & Senado)";
        const rows = GOLD.outliers.filter(r => JSON.stringify(r).toLowerCase().includes(q));
        box.innerHTML = `<table class="w-full text-left text-xs border-collapse">
          <thead><tr class="border-b border-slate-800 text-slate-400">
            <th class="py-2 pr-3">Casa / Parlamentar</th><th class="py-2 pr-3">Rubrica (Traduzida)</th><th class="py-2 pr-3">Fornecedor (CNPJ)</th><th class="py-2 pr-3 text-right">Valor da Nota</th><th class="py-2 pr-3 text-right">Mediana Rubrica</th><th class="py-2 pr-3 text-right">Z-Score / Múltiplo</th><th class="py-2 text-right">Prova Oficial</th>
          </tr></thead>
          <tbody class="divide-y divide-slate-800/70">${rows.map(r => `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 pr-3"><div class="font-semibold text-white">${r.parlamentar} (${r.partido}-${r.uf})</div><div class="text-slate-400">${r.casa} • ${r.data}</div></td>
              <td class="py-2.5 pr-3"><div class="font-medium text-emerald-300">${r.humano}</div><div class="text-slate-400">${r.rubrica}</div></td>
              <td class="py-2.5 pr-3"><div class="font-medium text-slate-200">${r.fornecedor}</div><div class="font-mono text-slate-400">${r.cnpj}</div></td>
              <td class="py-2.5 pr-3 text-right font-bold text-white">${fmtBRL(r.valor)}</td>
              <td class="py-2.5 pr-3 text-right text-slate-300">${fmtBRL(r.mediana)}</td>
              <td class="py-2.5 pr-3 text-right"><span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">+${r.z} DP (${r.mult}x)</span></td>
              <td class="py-2.5 text-right">${r.url ? `<a href="${r.url}" target="_blank" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-emerald-600 text-slate-200 hover:text-white font-mono">Abrir NF ↗</a>` : ''}</td>
            </tr>`).join('')}</tbody></table>`;
      } else if (currentTab === 'conc') {
        title.textContent = "Trilha 3 • Concentração de Cota Parlamentar em Fornecedor Único (Share % no Gabinete)";
        const rows = GOLD.conc.filter(r => JSON.stringify(r).toLowerCase().includes(q));
        box.innerHTML = `<table class="w-full text-left text-xs border-collapse">
          <thead><tr class="border-b border-slate-800 text-slate-400">
            <th class="py-2 pr-3">Parlamentar</th><th class="py-2 pr-3">Fornecedor Concentrado</th><th class="py-2 pr-3">Rubrica Predominante</th><th class="py-2 pr-3 text-right">Pago ao CNPJ</th><th class="py-2 pr-3 text-right">Total do Gabinete</th><th class="py-2 pr-3 text-right">% Concentrado</th><th class="py-2 text-right">Documento</th>
          </tr></thead>
          <tbody class="divide-y divide-slate-800/70">${rows.map(r => `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 pr-3"><div class="font-semibold text-white">${r.parlamentar} (${r.partido}-${r.uf})</div><div class="text-slate-400">${r.casa}</div></td>
              <td class="py-2.5 pr-3"><div class="font-medium text-white">${r.fornecedor}</div><div class="font-mono text-slate-400">CNPJ: ${r.cnpj} (${r.notas} notas)</div></td>
              <td class="py-2.5 pr-3 text-slate-300">${r.rubrica}</td>
              <td class="py-2.5 pr-3 text-right font-bold text-white">${fmtBRL(r.total_forn)}</td>
              <td class="py-2.5 pr-3 text-right text-slate-400">${fmtBRL(r.total_gab)}</td>
              <td class="py-2.5 pr-3 text-right"><span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">${r.share}% da cota</span></td>
              <td class="py-2.5 text-right"><a href="${r.url}" target="_blank" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-emerald-600 text-slate-200 font-mono">Prova ↗</a></td>
            </tr>`).join('')}</tbody></table>`;
      } else if (currentTab === 'pncp') {
        title.textContent = "Trilha 1 • Dispensas de Licitação no PNCP (Lei nº 14.133/2021, Art. 75 — Fracionamento e Limiares)";
        const rows = GOLD.pncp.filter(r => JSON.stringify(r).toLowerCase().includes(q));
        box.innerHTML = `<table class="w-full text-left text-xs border-collapse">
          <thead><tr class="border-b border-slate-800 text-slate-400">
            <th class="py-2 pr-3">Órgão / Município</th><th class="py-2 pr-3">Amparo Legal & Objeto</th><th class="py-2 pr-3 text-right">Valor da Dispensa</th><th class="py-2 pr-3 text-right">% do Teto Art. 75</th><th class="py-2 pr-3 text-right">Acúmulo no Órgão</th><th class="py-2 pr-3">Diagnóstico Determinístico</th><th class="py-2 text-right">PNCP</th>
          </tr></thead>
          <tbody class="divide-y divide-slate-800/70">${rows.map(r => `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 pr-3"><div class="font-semibold text-white">${r.orgao}</div><div class="text-slate-400">${r.municipio} - ${r.uf} • ${r.data}</div></td>
              <td class="py-2.5 pr-3"><div class="font-medium text-emerald-300">${r.amparo}</div><div class="text-slate-300">${r.objeto}</div></td>
              <td class="py-2.5 pr-3 text-right font-bold text-white">${fmtBRL(r.valor)}</td>
              <td class="py-2.5 pr-3 text-right font-mono text-amber-300">${r.pct_teto}%</td>
              <td class="py-2.5 pr-3 text-right"><div class="font-semibold text-white">${fmtBRL(r.soma_orgao)}</div><div class="text-slate-400">${r.qtd_orgao} dispensa(s)</div></td>
              <td class="py-2.5 pr-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-amber-300">${r.diag}</span></td>
              <td class="py-2.5 text-right"><a href="${r.url}" target="_blank" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-emerald-600 text-slate-200 font-mono">Edital ↗</a></td>
            </tr>`).join('')}</tbody></table>`;
      } else {
        title.textContent = "Portal Cívico • Tradutor de 'Orçamentês' e Estatísticas de Referência por Rubrica";
        const rows = GOLD.rubricas.filter(r => JSON.stringify(r).toLowerCase().includes(q));
        box.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-3">${rows.map(r => `
          <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">${r.casa}</span>
              <span class="text-xs font-bold text-emerald-400">Total: ${fmtBRL(r.total)}</span>
            </div>
            <div class="text-sm font-bold text-white">${r.humano}</div>
            <div class="text-xs font-mono text-slate-400">Rubrica Oficial: ${r.rubrica}</div>
            <p class="text-xs text-slate-300">${r.explicacao}</p>
            <div class="grid grid-cols-3 gap-2 pt-2 border-t border-slate-900 text-xs">
              <div><span class="text-slate-500">Mediana:</span> <strong class="text-white">${fmtBRL(r.mediana)}</strong></div>
              <div><span class="text-slate-500">IQR:</span> <strong class="text-white">${fmtBRL(r.iqr)}</strong></div>
              <div><span class="text-slate-500">Maior Nota:</span> <strong class="text-amber-400">${fmtBRL(r.maior)}</strong></div>
            </div>
          </div>`).join('')}</div>`;
      }
    }

    initKPIs();
    renderCurrentTab();
  </script>
</body>
</html>
"""


def main() -> None:
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    payload = LEAN_JSON.read_text(encoding="utf-8")
    html = TEMPLATE.replace("__GOLD_PAYLOAD__", payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Dashboard gerado com sucesso em: {OUT_HTML} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()

