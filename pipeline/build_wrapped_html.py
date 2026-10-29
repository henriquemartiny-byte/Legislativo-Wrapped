"""
Compilador do Vogon Wrapped com:
- Filtro Triplo: Casa Legislativa (Câmara vs Senado) × Estado (UF) × Partido Político
- Design System Oficial do Spotify Wrapped (Pitch Black, Verde Spotify, Amarelo, Roxo, Laranja)
- Modo Stories Interativo
- Playlist com ordenação e cálculo dinâmico de bancadas partidárias.
"""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "pipeline" / "storage" / "gold" / "vogon_wrapped_data.json"
OUT_HTML = ROOT / "web" / "wrapped.html"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Legislativo Wrapped 2025 • Retrospectiva dos Gastos Públicos</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #000000;
      color: #ffffff;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }
    
    .card-yellow {
      background: linear-gradient(145deg, #f6dc35 0%, #eab308 100%);
      color: #000000;
    }
    .card-purple {
      background: linear-gradient(145deg, #8c52ff 0%, #5b21b6 100%);
      color: #ffffff;
    }
    .card-orange {
      background: linear-gradient(145deg, #ff4632 0%, #dc2626 100%);
      color: #ffffff;
    }
    .card-green {
      background: linear-gradient(145deg, #1ed760 0%, #065f46 100%);
      color: #000000;
    }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #121212; }
    ::-webkit-scrollbar-thumb { background: #282828; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3e3e3e; }
  </style>
</head>
<body class="bg-black text-white min-h-screen antialiased selection:bg-[#1ed760] selection:text-black">

  <!-- Spotify Header Bar -->
  <nav class="sticky top-0 z-40 bg-black/85 backdrop-blur-md border-b border-white/10 px-4 md:px-8 py-3.5 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-full bg-[#1ed760] flex items-center justify-center text-black font-black text-lg">
        L
      </div>
      <div class="flex flex-col">
        <span class="text-xs font-black tracking-widest text-[#1ed760] uppercase">LEGISLATIVO WRAPPED 2025</span>
        <span class="text-[11px] text-zinc-400 font-medium">Retrospectiva Oficial da Cota Parlamentar</span>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      <span class="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-[#1ed760]/10 text-[#1ed760] border border-[#1ed760]/30">
        100% DETERMINÍSTICO
      </span>
    </div>
  </nav>

  <main class="max-w-6xl mx-auto px-4 md:px-8 py-8 space-y-10">

    <!-- Hero Spotify Wrapped Title -->
    <header class="space-y-4">
      <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/10 text-white text-xs font-extrabold uppercase tracking-widest">
        #RetrospectivaParlamentar
      </div>
      <h1 class="text-4xl md:text-6xl font-black tracking-tighter leading-none text-white">
        O seu 2025 no <br />
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-[#1ed760] via-[#8c52ff] to-[#ff4632]">
          Congresso Nacional.
        </span>
      </h1>
      <p class="text-sm md:text-base text-zinc-400 max-w-2xl font-medium">
        Auditamos 193.825 notas fiscais e R$ 251 milhões reembolsados aos parlamentares. 
        Cruze por <span class="text-[#1ed760] font-bold">Casa</span>, <span class="text-[#f6dc35] font-bold">Estado</span> e <span class="text-[#8c52ff] font-bold">Partido Político</span> para comparar quem mais gastou dinheiro público.
      </p>
    </header>

    <!-- Buscador Spotify Style (No Topo da Página) -->
    <section class="bg-[#121212] rounded-3xl p-6 md:p-7 space-y-4 border border-white/10 shadow-2xl">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <span class="text-xs font-black text-[#1ed760] uppercase tracking-wider">BUSCA DIRETA SPOTIFY</span>
          <h2 class="text-2xl font-black text-white tracking-tight mt-0.5">Buscar Qualquer Deputado ou Senador</h2>
          <p class="text-xs text-zinc-400 mt-1">Consulte o dossiê individual e notas atípicas de qualquer um dos 645 parlamentares auditados</p>
        </div>
        <div class="w-full md:w-96 relative">
          <input type="text" id="parl-search" oninput="searchParl(this.value)" placeholder="Digite o nome (ex: Nikolas, Tabata, Gabriel Mota...)" class="w-full pl-11 pr-5 py-3 text-xs md:text-sm font-bold rounded-full bg-[#1e1e1e] border border-white/10 text-white placeholder-zinc-500 focus:outline-none focus:border-[#1ed760] focus:ring-1 focus:ring-[#1ed760] transition" />
          <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          </div>
        </div>
      </div>
      <div id="single-parl-card" class="empty:hidden"></div>
    </section>

    <!-- Controles em Pílulas: Casa + UF + Partido + Modo de Custo -->
    <section class="space-y-4">
      <div class="bg-[#121212] p-5 rounded-2xl border border-white/5 space-y-4">
        
        <!-- Alternador de Modo de Avaliação e Filtro de Titulares -->
        <div class="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-white/10">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-black uppercase tracking-wider text-zinc-300">Modo de Avaliação:</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#1ed760]/20 text-[#1ed760] font-mono font-bold">⭐ MANDATOS TITULARES EM EXERCÍCIO</span>
            </div>
            <p class="text-[11px] text-zinc-500 font-medium mt-0.5">Por padrão, avalia apenas os 513 deputados e 81 senadores titulares para não rebaixar as médias anuais com suplentes de 1 mês</p>
          </div>
          
          <div class="flex flex-wrap items-center gap-2">
            <!-- Alternador de Condição (Titular vs Todos) -->
            <div class="flex items-center gap-1 p-1 bg-[#181818] rounded-xl border border-white/10 text-xs">
              <button onclick="setCondicao('TITULAR')" id="btn-cond-titular" class="px-3 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md">
                Titulares (594)
              </button>
              <button onclick="setCondicao('TODOS')" id="btn-cond-todos" class="px-3 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white">
                Com Suplentes (645)
              </button>
            </div>

            <!-- Alternador de Escopo de Custo (Cota vs Total) -->
            <div class="flex items-center gap-1 p-1 bg-[#181818] rounded-xl border border-white/10 text-xs">
              <button onclick="setModoCusto('cota')" id="btn-modo-cota" class="px-3 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md">
                ✈️ Cota (CEAP)
              </button>
              <button onclick="setModoCusto('total')" id="btn-modo-total" class="px-3 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white">
                💼 Custo Total
              </button>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 1. Casa Legislativa -->
          <div>
            <label class="block text-xs font-extrabold uppercase tracking-wider text-zinc-400 mb-2">1. Casa Legislativa:</label>
            <div class="grid grid-cols-2 gap-2">
              <button onclick="setCasa('Câmara dos Deputados')" id="btn-camara" class="py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#1ed760] text-black shadow-lg">
                Câmara (513)
              </button>
              <button onclick="setCasa('Senado Federal')" id="btn-senado" class="py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#242424] text-white hover:bg-[#2e2e2e]">
                Senado (81)
              </button>
            </div>
          </div>

          <!-- 2. Estado (UF) -->
          <div>
            <label class="block text-xs font-extrabold uppercase tracking-wider text-zinc-400 mb-2">2. Estado (UF):</label>
            <select id="uf-select" onchange="setUF(this.value)" class="w-full py-2.5 px-4 rounded-xl text-xs font-extrabold bg-[#242424] border border-white/10 text-white focus:outline-none focus:border-[#1ed760] cursor-pointer">
              <option value="BR">🇧🇷 Brasil (Todos os Estados)</option>
            </select>
          </div>

          <!-- 3. Partido Político -->
          <div>
            <label class="block text-xs font-extrabold uppercase tracking-wider text-zinc-400 mb-2">3. Partido Político:</label>
            <select id="partido-select" onchange="setPartido(this.value)" class="w-full py-2.5 px-4 rounded-xl text-xs font-extrabold bg-[#242424] border border-white/10 text-[#1ed760] focus:outline-none focus:border-[#1ed760] cursor-pointer">
              <option value="TODOS">⚡ Todos os Partidos</option>
            </select>
          </div>
        </div>

        <!-- Atalhos Rápidos dos Principais Partidos -->
        <div class="pt-2 border-t border-white/5 flex flex-wrap items-center gap-1.5 text-xs">
          <span class="text-zinc-500 font-bold uppercase tracking-wider text-[10px] mr-1">Atalhos Partidários:</span>
          <button onclick="setPartido('TODOS')" id="chip-part-TODOS" class="px-2.5 py-1 rounded-full text-xs font-black bg-[#1ed760] text-black">Todos</button>
          <button onclick="setPartido('PL')" id="chip-part-PL" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PL</button>
          <button onclick="setPartido('PT')" id="chip-part-PT" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PT</button>
          <button onclick="setPartido('UNIÃO')" id="chip-part-UNIÃO" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">UNIÃO</button>
          <button onclick="setPartido('PP')" id="chip-part-PP" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PP</button>
          <button onclick="setPartido('PSD')" id="chip-part-PSD" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PSD</button>
          <button onclick="setPartido('MDB')" id="chip-part-MDB" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">MDB</button>
          <button onclick="setPartido('REPUBLICANOS')" id="chip-part-REPUBLICANOS" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">REP</button>
          <button onclick="setPartido('PSB')" id="chip-part-PSB" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PSB</button>
          <button onclick="setPartido('PSOL')" id="chip-part-PSOL" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">PSOL</button>
          <button onclick="setPartido('NOVO')" id="chip-part-NOVO" class="px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white">NOVO</button>
          <button onclick="togglePartyComparison()" id="btn-toggle-part-comp" class="ml-auto px-3 py-1 rounded-full text-xs font-black bg-[#1ed760]/10 text-[#1ed760] hover:bg-[#1ed760]/20 flex items-center gap-1.5 border border-[#1ed760]/20 transition">
            <span>📊 Ranking Per Capita dos Partidos</span>
            <span id="party-comp-arrow">▼</span>
          </button>
        </div>

        <!-- Tabela Expansível de Comparativo Partidário (Média por Parlamentar) -->
        <div id="party-comparison-container" class="hidden pt-4 border-t border-white/5 space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="text-sm font-black text-white flex items-center gap-2">
                <span>Gastos Médios por Parlamentar (Ranking Per Capita)</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-zinc-300 font-mono font-bold" id="party-comp-scope-badge">Câmara</span>
              </h4>
              <p class="text-[11px] text-zinc-400">Normalizado pelo tamanho da bancada para eliminar distorções de volume.</p>
            </div>
            <button onclick="togglePartyComparison()" class="text-zinc-500 hover:text-white text-xs font-bold">Fechar ✕</button>
          </div>
          <div id="party-comparison-table" class="overflow-x-auto max-h-72 overflow-y-auto"></div>
        </div>

      </div>
    </section>

    <!-- Banner Editorial de Estatísticas da Seleção -->
    <div id="state-banner" class="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[#121212] border border-white/5 text-xs md:text-sm"></div>

    <!-- Os 4 Cartões Wrapped Estilo Spotify -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-5" id="cards-container"></section>

    <!-- Playlist do Spotify: Tabela de Parlamentares Filtrados -->
    <section class="bg-[#121212] rounded-3xl p-6 md:p-8 space-y-6 border border-white/5">
      <div class="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <span class="text-xs font-extrabold text-[#1ed760] uppercase tracking-wider">CLASSIFICAÇÃO OFICIAL DA BANCADA</span>
          <h2 class="text-2xl font-black text-white tracking-tight mt-0.5">
            Gastos por Parlamentar • <span id="ranking-title-uf"></span>
          </h2>
          <p class="text-xs text-zinc-400 mt-1">Clique em qualquer linha para abrir o Stories com o dossiê individual do político</p>
        </div>
        <div class="text-xs text-zinc-400 font-mono" id="table-count-badge"></div>
      </div>

      <div id="podio-table" class="overflow-x-auto"></div>
    </section>

    <!-- Footer Spotify Style -->
    <footer class="pt-10 border-t border-white/10 text-center text-xs text-zinc-600 space-y-2 pb-12">
      <p class="font-bold text-zinc-400">LEGISLATIVO WRAPPED • INSPIRAÇÃO SPOTIFY DESIGN SYSTEM</p>
      <p>Auditoria Algorítmica 100% Determinística (Python + Polars + DuckDB) • Exercício 2025</p>
    </footer>

  </main>

  <!-- MODAL: STORIES DE GASTOS DO PARLAMENTAR -->
  <div id="modal-stories" class="fixed inset-0 z-50 hidden bg-black/95 backdrop-blur-xl flex items-center justify-center p-4">
    <div class="relative w-full max-w-md h-[680px] rounded-[32px] overflow-hidden flex flex-col justify-between p-6 shadow-2xl border border-white/10" id="story-card-wrapper">
      
      <div class="flex items-center gap-1.5 z-20">
        <div class="h-1 flex-1 rounded-full bg-white/30 overflow-hidden"><div id="prog-1" class="h-full bg-white w-full transition-all duration-300"></div></div>
        <div class="h-1 flex-1 rounded-full bg-white/30 overflow-hidden"><div id="prog-2" class="h-full bg-white w-0 transition-all duration-300"></div></div>
        <div class="h-1 flex-1 rounded-full bg-white/30 overflow-hidden"><div id="prog-3" class="h-full bg-white w-0 transition-all duration-300"></div></div>
        <div class="h-1 flex-1 rounded-full bg-white/30 overflow-hidden"><div id="prog-4" class="h-full bg-white w-0 transition-all duration-300"></div></div>
      </div>

      <button onclick="closeStories()" class="absolute top-5 right-5 z-20 w-8 h-8 rounded-full bg-black/40 hover:bg-black/60 flex items-center justify-center text-white text-xs font-bold">
        ✕
      </button>

      <div id="story-content" class="flex-1 flex flex-col justify-center py-6 z-10 text-center"></div>

      <div class="flex items-center justify-between pt-4 border-t border-white/10 z-20">
        <button onclick="prevStory()" class="px-4 py-2 rounded-full text-xs font-bold bg-white/10 hover:bg-white/20 text-white transition">
          ← Anterior
        </button>
        <span id="story-counter" class="text-xs font-mono text-white/60">1 / 4</span>
        <button onclick="nextStory()" class="px-4 py-2 rounded-full text-xs font-bold bg-white text-black hover:bg-[#1ed760] transition">
          Próximo →
        </button>
      </div>

      <div onclick="prevStory()" class="absolute inset-y-16 left-0 w-1/3 z-0 cursor-pointer"></div>
      <div onclick="nextStory()" class="absolute inset-y-16 right-0 w-1/3 z-0 cursor-pointer"></div>
    </div>
  </div>

  <!-- MODAL: DIAGNÓSTICO FORENSE DA NOTA FISCAL -->
  <div id="modal-nota" class="fixed inset-0 z-50 hidden bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
    <div class="bg-[#121212] border border-white/10 rounded-3xl max-w-lg w-full p-6 md:p-8 space-y-6 shadow-2xl relative">
      <button onclick="closeModal('modal-nota')" class="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#242424] hover:bg-[#2e2e2e] flex items-center justify-center text-zinc-300 text-xs font-bold">
        ✕
      </button>
      <div id="modal-nota-body"></div>
    </div>
  </div>

  <script>
    const DATA = __DATA_PAYLOAD__;
    let selectedCasa = "Câmara dos Deputados";
    let selectedUF = "BR";
    let selectedPartido = "TODOS";
    
    let currentStoryParl = null;
    let currentStoryStep = 1;

    const fmtBRL = (v) => Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    function initFilters() {
      // 1. UFs
      const selUF = document.getElementById('uf-select');
      DATA.ufs.forEach(uf => {
        const opt = document.createElement('option');
        opt.value = uf;
        opt.textContent = `${uf} - Bancada Estadual`;
        selUF.appendChild(opt);
      });

      // 2. Partidos
      const selPart = document.getElementById('partido-select');
      const partySet = new Set();
      DATA.parlamentares.forEach(p => {
        if (p.partido && p.partido !== 'S/P' && p.partido !== 'S/Partido' && p.partido !== 'SENADO') {
          partySet.add(p.partido);
        }
      });
      const sortedPartidos = Array.from(partySet).sort();
      sortedPartidos.forEach(part => {
        const opt = document.createElement('option');
        opt.value = part;
        opt.textContent = `${part} • Partido`;
        selPart.appendChild(opt);
      });
    }

    let selectedModoCusto = "cota"; // 'cota' ou 'total'
    let selectedCondicao = "TITULAR"; // 'TITULAR' (padrão) ou 'TODOS'

    function setCondicao(cond) {
      selectedCondicao = cond;
      const btnTit = document.getElementById('btn-cond-titular');
      const btnAll = document.getElementById('btn-cond-todos');
      if (btnTit && btnAll) {
        if (cond === 'TITULAR') {
          btnTit.className = "px-3 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md";
          btnAll.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white";
        } else {
          btnTit.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white";
          btnAll.className = "px-3 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md";
        }
      }
      render();
    }

    function setModoCusto(modo) {
      selectedModoCusto = modo;
      const btnCota = document.getElementById('btn-modo-cota');
      const btnTotal = document.getElementById('btn-modo-total');
      if (btnCota && btnTotal) {
        if (modo === 'cota') {
          btnCota.className = "px-3.5 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md flex items-center gap-1.5";
          btnTotal.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white flex items-center gap-1.5";
        } else {
          btnCota.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition bg-transparent text-zinc-400 hover:text-white flex items-center gap-1.5";
          btnTotal.className = "px-3.5 py-1.5 rounded-lg text-xs font-black transition bg-[#1ed760] text-black shadow-md flex items-center gap-1.5";
        }
      }
      render();
    }

    function setCasa(casa) {
      selectedCasa = casa;
      document.getElementById('btn-camara').className = (casa === 'Câmara dos Deputados')
        ? "py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#1ed760] text-black shadow-lg"
        : "py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#242424] text-white hover:bg-[#2e2e2e]";
      document.getElementById('btn-senado').className = (casa === 'Senado Federal')
        ? "py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#1ed760] text-black shadow-lg"
        : "py-2.5 px-3 rounded-xl text-xs font-extrabold transition bg-[#242424] text-white hover:bg-[#2e2e2e]";
      render();
    }

    function setUF(uf) {
      selectedUF = uf;
      document.getElementById('uf-select').value = uf;
      render();
    }

    function setPartido(part) {
      selectedPartido = part;
      document.getElementById('partido-select').value = part;

      // Atualiza os botões de atalho
      ['TODOS', 'PL', 'PT', 'UNIÃO', 'PP', 'PSD', 'MDB', 'REPUBLICANOS', 'PSB', 'PSOL', 'NOVO'].forEach(p => {
        const chip = document.getElementById('chip-part-' + p);
        if (chip) {
          chip.className = (p === part)
            ? "px-2.5 py-1 rounded-full text-xs font-black bg-[#1ed760] text-black"
            : "px-2.5 py-1 rounded-full text-xs font-bold bg-[#242424] text-zinc-300 hover:text-white";
        }
      });

      render();
    }

    function closeModal(id) {
      document.getElementById(id).classList.add('hidden');
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeModal('modal-nota');
        closeStories();
      }
      if (!document.getElementById('modal-stories').classList.contains('hidden')) {
        if (e.key === 'ArrowRight') nextStory();
        if (e.key === 'ArrowLeft') prevStory();
      }
    });

    function togglePartyComparison() {
      const container = document.getElementById('party-comparison-container');
      const arrow = document.getElementById('party-comp-arrow');
      if (container.classList.contains('hidden')) {
        container.classList.remove('hidden');
        if (arrow) arrow.textContent = '▲';
        renderPartyComparison();
      } else {
        container.classList.add('hidden');
        if (arrow) arrow.textContent = '▼';
      }
    }

    function renderPartyComparison() {
      const badge = document.getElementById('party-comp-scope-badge');
      if (badge) {
        badge.textContent = `${selectedCasa} • ${(selectedUF === 'BR') ? 'Brasil' : selectedUF}`;
      }

      // Agrupa parlamentares do escopo (Casa x UF x Condição) por partido
      const partyMap = {};
      DATA.parlamentares.forEach(p => {
        if (selectedCondicao === 'TITULAR' && !p.is_titular) return;
        if (selectedCasa !== 'TODAS' && p.casa !== selectedCasa) return;
        if (selectedUF !== 'BR' && p.uf !== selectedUF) return;
        const sigla = p.partido || 'OUTROS';
        const val = (selectedModoCusto === 'total') ? (p.custo_total_mandato || p.total) : p.total;
        if (!partyMap[sigla]) {
          partyMap[sigla] = { partido: sigla, total: 0, parlamentares: 0, outliers: 0, maxGasto: 0, topNome: '' };
        }
        partyMap[sigla].total += val;
        partyMap[sigla].parlamentares += 1;
        partyMap[sigla].outliers += (p.outliers_z3 || 0);
        if (val > partyMap[sigla].maxGasto) {
          partyMap[sigla].maxGasto = val;
          partyMap[sigla].topNome = p.nome;
        }
      });

      const partyList = Object.values(partyMap).map(item => ({
        ...item,
        media: item.parlamentares > 0 ? (item.total / item.parlamentares) : 0
      })).sort((a, b) => b.media - a.media);

      const maxMedia = partyList.length > 0 ? partyList[0].media : 1;

      let html = `
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="text-[10px] text-zinc-500 font-bold uppercase tracking-wider border-b border-white/10 pb-2">
              <th class="py-2 pl-3">#</th>
              <th class="py-2">Partido</th>
              <th class="py-2 text-center">Bancada</th>
              <th class="py-2">Gasto Médio / Parlamentar</th>
              <th class="py-2">Total do Partido</th>
              <th class="py-2 text-center">Notas Fora do Padrão</th>
              <th class="py-2 pr-3 text-right">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
      `;

      partyList.forEach((pt, idx) => {
        const pctBar = maxMedia > 0 ? Math.min(100, Math.round((pt.media / maxMedia) * 100)) : 0;
        const isCurrent = (pt.partido === selectedPartido);
        html += `
          <tr class="hover:bg-white/[0.03] transition ${isCurrent ? 'bg-[#1ed760]/10' : ''}">
            <td class="py-3 pl-3 font-mono font-bold text-zinc-400">#${idx + 1}</td>
            <td class="py-3">
              <span class="px-2.5 py-1 rounded-md bg-[#242424] text-white font-black text-xs border border-white/10">
                ${pt.partido}
              </span>
            </td>
            <td class="py-3 text-center font-bold text-zinc-300">
              ${pt.parlamentares} ${pt.parlamentares === 1 ? 'membro' : 'membros'}
            </td>
            <td class="py-3 min-w-[220px]">
              <div class="flex items-center gap-3">
                <span class="font-mono font-black text-[#1ed760] text-sm">${fmtBRL(pt.media)}</span>
              </div>
              <div class="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-1">
                <div class="bg-[#1ed760] h-full rounded-full" style="width: ${pctBar}%"></div>
              </div>
            </td>
            <td class="py-3 font-mono font-bold text-zinc-300">${fmtBRL(pt.total)}</td>
            <td class="py-3 text-center font-mono ${pt.outliers > 0 ? 'text-[#ff4632] font-black' : 'text-zinc-500'}">
              ${pt.outliers}
            </td>
            <td class="py-3 pr-3 text-right">
              <button onclick="setPartido('${pt.partido}'); togglePartyComparison();" class="px-3 py-1 rounded-full text-[11px] font-bold bg-[#242424] hover:bg-[#1ed760] hover:text-black text-white transition border border-white/10">
                Ver no Wrapped ↗
              </button>
            </td>
          </tr>
        `;
      });

      html += `
          </tbody>
        </table>
      `;

      const target = document.getElementById('party-comparison-table');
      if (target) target.innerHTML = html;
    }

    function render() {
      // Filtra dinamicamente os parlamentares com base em Condição (Titular/Suplente), Casa × UF × Partido e Modo de Custo
      const filtered = DATA.parlamentares.filter(p => {
        if (selectedCondicao === 'TITULAR' && !p.is_titular) return false;
        if (selectedCasa !== 'TODAS' && p.casa !== selectedCasa) return false;
        if (selectedUF !== 'BR' && p.uf !== selectedUF) return false;
        if (selectedPartido !== 'TODOS' && p.partido !== selectedPartido) return false;
        return true;
      }).sort((a, b) => {
        const valA = (selectedModoCusto === 'total') ? (a.custo_total_mandato || a.total) : a.total;
        const valB = (selectedModoCusto === 'total') ? (b.custo_total_mandato || b.total) : b.total;
        return valB - valA;
      });

      // Título do escopo
      let titleScope = (selectedUF === 'BR') ? 'Bancada Nacional' : selectedUF;
      if (selectedPartido !== 'TODOS') {
        titleScope += ` • Partido ${selectedPartido}`;
      }
      titleScope += (selectedCondicao === 'TITULAR') ? ' • [Apenas Titulares]' : ' • [Com Suplentes]';
      titleScope += (selectedModoCusto === 'total') ? ' • [Custo Total de Gabinete]' : ' • [Cota Operacional CEAP]';
      document.getElementById('ranking-title-uf').textContent = titleScope;

      const totalGasto = filtered.reduce((acc, p) => {
        const val = (selectedModoCusto === 'total') ? (p.custo_total_mandato || p.total) : p.total;
        return acc + val;
      }, 0);
      const totalNotas = filtered.reduce((acc, p) => acc + p.notas, 0);
      const totalOutliers = filtered.reduce((acc, p) => acc + (p.outliers_z3 || 0), 0);
      const totalAssessores = filtered.reduce((acc, p) => acc + (p.qtd_assessores || 0), 0);
      const countParl = filtered.length;

      // Cálculo rigoroso de médias per capita e baseline da Casa considerando a condição selecionada
      const allCasa = DATA.parlamentares.filter(p => {
        if (selectedCondicao === 'TITULAR' && !p.is_titular) return false;
        if (selectedCasa !== 'TODAS' && p.casa !== selectedCasa) return false;
        return true;
      });
      const totalCasa = allCasa.reduce((acc, p) => {
        const val = (selectedModoCusto === 'total') ? (p.custo_total_mandato || p.total) : p.total;
        return acc + val;
      }, 0);
      const mediaGeralCasa = allCasa.length > 0 ? (totalCasa / allCasa.length) : 0;

      const mediaGasto = countParl > 0 ? (totalGasto / countParl) : 0;
      const diffVsMedia = mediaGeralCasa > 0 ? (((mediaGasto - mediaGeralCasa) / mediaGeralCasa) * 100) : 0;
      const diffSign = diffVsMedia >= 0 ? `+${diffVsMedia.toFixed(1)}%` : `${diffVsMedia.toFixed(1)}%`;
      const diffBadge = (selectedPartido !== 'TODOS')
        ? `<div class="text-[10px] font-bold ${diffVsMedia > 0 ? 'text-amber-400' : 'text-emerald-400'} mt-0.5">${diffSign} vs média geral (${fmtBRL(mediaGeralCasa)})</div>`
        : `<div class="text-[10px] font-bold text-zinc-500 mt-0.5">Média geral da Casa: ${fmtBRL(mediaGeralCasa)}</div>`;

      document.getElementById('table-count-badge').textContent = `${countParl} parlamentares encontrados`;

      // Atualiza o ranking per capita se a gaveta estiver aberta
      const partCompContainer = document.getElementById('party-comparison-container');
      if (partCompContainer && !partCompContainer.classList.contains('hidden')) {
        renderPartyComparison();
      }

      // Banner Editorial
      document.getElementById('state-banner').innerHTML = `
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-2xl bg-[#181818] border border-white/10 flex items-center justify-center font-black text-[#1ed760] text-sm">
            ${selectedPartido !== 'TODOS' ? selectedPartido.slice(0, 4) : ((selectedUF === 'BR') ? 'BR' : selectedUF)}
          </div>
          <div>
            <div class="text-xs text-zinc-400 font-semibold">Recorte Selecionado</div>
            <div class="text-base font-extrabold text-white">
              ${selectedCasa} • ${(selectedUF === 'BR') ? 'Brasil' : selectedUF} • ${selectedPartido !== 'TODOS' ? selectedPartido : 'Todos os Partidos'}
            </div>
          </div>
        </div>
        <div>
          <div class="text-xs text-zinc-400 font-semibold">
            ${selectedModoCusto === 'total' ? 'Custo Total de Gabinete' : 'Total Reembolsado (Cota)'}
          </div>
          <div class="text-xl font-black text-[#1ed760] font-mono">${fmtBRL(totalGasto)}</div>
        </div>
        <div>
          <div class="text-xs text-zinc-400 font-semibold">Bancada & Equipe</div>
          <div class="text-xl font-black text-white">${countParl} ${countParl === 1 ? 'parlamentar' : 'parlamentares'} <span class="text-[#1ed760] font-mono text-xs block">${totalAssessores} assessores</span></div>
        </div>
        <div class="bg-white/[0.04] px-4 py-2.5 rounded-2xl border border-white/10">
          <div class="text-[11px] text-zinc-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <span>Média por Parlamentar</span>
            <span class="text-[9px] bg-[#1ed760]/20 text-[#1ed760] px-1.5 py-0.5 rounded font-mono font-black">PER CAPITA</span>
          </div>
          <div class="text-xl font-black text-[#1ed760] font-mono mt-0.5">${fmtBRL(mediaGasto)}</div>
          ${diffBadge}
        </div>
        <div>
          <div class="text-xs text-zinc-400 font-semibold">Recibos Fora do Padrão</div>
          <div class="text-xl font-black text-[#ff4632]">${totalOutliers} notas</div>
        </div>
      `;

      if (filtered.length === 0) {
        document.getElementById('cards-container').innerHTML = `
          <div class="col-span-2 p-10 rounded-3xl bg-[#121212] border border-white/10 text-center space-y-2">
            <div class="text-3xl">🔍</div>
            <h3 class="text-lg font-bold text-white">Nenhum parlamentar encontrado para esta combinação</h3>
            <p class="text-xs text-zinc-400">O partido ${selectedPartido} não possui representantes eleitos em ${selectedUF} nesta casa legislativa.</p>
          </div>
        `;
        document.getElementById('podio-table').innerHTML = '<div class="text-xs text-zinc-500 py-6 text-center">Nenhum registro para exibir.</div>';
        return;
      }

      // Campeão do Recorte
      const c = filtered[0] || {};
      
      // Top Fornecedor do Recorte
      const supplierMap = {};
      filtered.forEach(p => {
        (p.top_fornecedores || []).forEach(f => {
          if (!supplierMap[f.cnpj]) {
            supplierMap[f.cnpj] = { nome: f.nome, cnpj: f.cnpj, logo: f.logo, total: 0, notas: 0, parlamentares: 0 };
          }
          supplierMap[f.cnpj].total += f.total;
          supplierMap[f.cnpj].notas += f.notas;
          supplierMap[f.cnpj].parlamentares += 1;
        });
      });
      const topSuppliers = Object.values(supplierMap).sort((a, b) => b.total - a.total);
      const f = topSuppliers[0] || (c.top_fornecedores && c.top_fornecedores[0]) || {};
      const fornShare = totalGasto > 0 ? ((f.total / totalGasto) * 100).toFixed(1) : 0;

      // Maior Nota do Recorte
      let maiorNotaObj = null;
      filtered.forEach(p => {
        (p.notas_atipicas || []).forEach(n => {
          if (!maiorNotaObj || n.valor > maiorNotaObj.valor) {
            maiorNotaObj = { ...n, parlamentar: p.nome, foto: p.foto, partido: p.partido, uf: p.uf };
          }
        });
      });
      const m = maiorNotaObj || (c.notas_atipicas && c.notas_atipicas[0]) || {
        valor: c.maior_nota || 0,
        parlamentar: c.nome,
        fornecedor: f.nome || 'Fornecedor',
        multiplo: 1
      };

      // Gênero / Categoria Predominante
      const rubricMap = {};
      filtered.forEach(p => {
        (p.top_fornecedores || []).forEach(tf => {
          const rub = tf.rubrica || 'DIVULGAÇÃO PARLAMENTAR';
          rubricMap[rub] = (rubricMap[rub] || 0) + tf.total;
        });
      });
      const topRubric = Object.entries(rubricMap).sort((a, b) => b[1] - a[1])[0] || ['DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR', totalGasto * 0.4];
      const rubricShare = totalGasto > 0 ? ((topRubric[1] / totalGasto) * 100).toFixed(1) : 0;

      const fallbackAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(c.nome || 'P')}&background=1ed760&color=000&bold=true`;
      const fallbackForn = `https://ui-avatars.com/api/?name=${encodeURIComponent(f.nome || 'E')}&background=8c52ff&color=fff&bold=true`;
      const fallbackMaior = `https://ui-avatars.com/api/?name=${encodeURIComponent(m.parlamentar || 'M')}&background=ff4632&color=fff&bold=true`;

      // Os 4 Cartões Wrapped com Cores Vivas do Spotify
      document.getElementById('cards-container').innerHTML = `
        
        <!-- CARD 1: Campeão de Gastos (Card Amarelo Vibrante) -->
        <div onclick="openStories('${c.nome}')" class="card-yellow rounded-[28px] p-7 flex flex-col justify-between space-y-6 cursor-pointer hover:scale-[1.01] transition-transform shadow-xl">
          <div class="flex items-center justify-between">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-black text-[#f6dc35]">
              #1 MAIS OUVIDO DO RECORTE
            </span>
            <span class="text-xs font-black tracking-wider uppercase font-mono">
              VER STORIES ↗
            </span>
          </div>

          <div class="flex items-center gap-5">
            <img src="${c.foto || fallbackAvatar}" onerror="this.src='${fallbackAvatar}'" class="w-20 h-20 rounded-full object-cover border-4 border-black shadow-2xl shrink-0" alt="${c.nome || ''}" />
            <div>
              <span class="text-xs font-bold tracking-wider uppercase opacity-80">${c.partido || ''} • ${c.uf || ''}</span>
              <h3 class="text-3xl font-black tracking-tight leading-tight mt-0.5">${c.nome || 'N/A'}</h3>
            </div>
          </div>

          <div class="pt-4 border-t border-black/20 flex items-end justify-between">
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider opacity-75">
                ${selectedModoCusto === 'total' ? 'Custo Total Integrado do Gabinete' : 'Total Reembolsado em 2025'}
              </div>
              <div class="text-3xl font-black tracking-tight">
                ${fmtBRL(selectedModoCusto === 'total' ? c.custo_total_mandato : c.total)}
              </div>
              ${selectedModoCusto === 'total' ? `<div class="text-[11px] font-black opacity-80 mt-0.5">Equipe: ${fmtBRL(c.custo_equipe_ano)} • Cota: ${fmtBRL(c.total)}</div>` : ''}
            </div>
            <div class="text-right">
              <div class="text-xs font-black">${c.qtd_assessores || 0} assessores na equipe</div>
              <div class="text-xs font-extrabold text-red-900">${c.outliers_z3 || 0} recibos fora do padrão</div>
            </div>
          </div>
        </div>

        <!-- CARD 2: Empresa Favorita (Card Roxo Elétrico) -->
        <div class="card-purple rounded-[28px] p-7 flex flex-col justify-between space-y-6 shadow-xl">
          <div class="flex items-center justify-between">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-white text-[#8c52ff]">
              FORNECEDOR FAVORITO
            </span>
            <span class="text-xs font-bold font-mono opacity-80">MAIS CONTRATADO</span>
          </div>

          <div class="flex items-center gap-4">
            <img src="${f.logo || fallbackForn}" onerror="this.src='${fallbackForn}'" class="w-16 h-16 rounded-2xl object-contain bg-white/20 p-2 shadow-lg shrink-0" alt="" />
            <div class="min-w-0">
              <div class="text-2xl font-black tracking-tight truncate">${f.nome || 'N/A'}</div>
              <div class="text-xs font-mono opacity-80 mt-0.5 truncate">CNPJ: ${f.cnpj || 'N/A'}</div>
            </div>
          </div>

          <div class="pt-4 border-t border-white/20 flex items-end justify-between">
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider opacity-75">Faturado com Este Grupo</div>
              <div class="text-3xl font-black tracking-tight">${fmtBRL(f.total)}</div>
            </div>
            <div class="text-right">
              <div class="text-xs font-black">${f.notas || 0} notas emitidas</div>
              <div class="text-xs font-extrabold text-[#1ed760]">${fornShare}% do dinheiro do grupo</div>
            </div>
          </div>
        </div>

        <!-- CARD 3: Gênero Mais Ouvido (Card Verde Spotify) -->
        <div class="card-green rounded-[28px] p-7 flex flex-col justify-between space-y-6 shadow-xl">
          <div class="flex items-center justify-between">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-black text-[#1ed760]">
              GÊNERO MAIS TOCADO
            </span>
            <span class="text-xs font-bold font-mono opacity-80">CATEGORIA DE GASTO</span>
          </div>

          <div class="space-y-1">
            <div class="text-2xl font-black tracking-tight leading-tight">${topRubric[0]}</div>
            <div class="text-xs font-bold opacity-80">A rubrica mais utilizada pelos parlamentares selecionados</div>
          </div>

          <div class="pt-4 border-t border-black/20 flex items-end justify-between">
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider opacity-75">Volume Gasto na Categoria</div>
              <div class="text-3xl font-black tracking-tight">${fmtBRL(topRubric[1])}</div>
            </div>
            <div class="text-right">
              <div class="text-xs font-black">${rubricShare}% de todo o orçamento</div>
            </div>
          </div>
        </div>

        <!-- CARD 4: Faixa Mais Cara (Card Laranja / Spotify Now Playing) -->
        <div onclick='openNotaModal(${JSON.stringify(m).replace(/'/g, "&#39;")})' class="card-orange rounded-[28px] p-7 flex flex-col justify-between space-y-6 cursor-pointer hover:scale-[1.01] transition-transform shadow-xl">
          <div class="flex items-center justify-between">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-black text-[#ff4632]">
              FAIXA MAIS CARA DO ANO
            </span>
            <span class="text-xs font-bold font-mono opacity-90 underline">VER EXPLICAÇÃO ℹ️</span>
          </div>

          <div class="flex items-center gap-4">
            <img src="${m.foto || fallbackMaior}" onerror="this.src='${fallbackMaior}'" class="w-16 h-16 rounded-full object-cover border-2 border-white shadow-xl shrink-0" alt="" />
            <div class="min-w-0">
              <div class="text-2xl font-black tracking-tight truncate">${m.parlamentar || 'N/A'}</div>
              <div class="text-xs font-medium opacity-90 truncate">${m.fornecedor || ''}</div>
            </div>
          </div>

          <!-- Player Scrubber Fictício -->
          <div class="space-y-1.5">
            <div class="h-1.5 w-full rounded-full bg-black/30 overflow-hidden">
              <div class="h-full bg-white w-4/5"></div>
            </div>
            <div class="flex items-center justify-between text-[10px] font-mono opacity-80">
              <span>VALOR DA NOTA</span>
              <span>${m.multiplo || 0}x A MEDIANA</span>
            </div>
          </div>

          <div class="flex items-end justify-between">
            <div>
              <div class="text-3xl font-black tracking-tight">${fmtBRL(m.valor)}</div>
            </div>
            <div class="text-right">
              <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-black text-white text-xs font-extrabold">
                ▶ Abrir Análise
              </span>
            </div>
          </div>
        </div>

      `;

      // Playlist Table com Todos os Parlamentares do Filtro
      document.getElementById('podio-table').innerHTML = `
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-white/10 text-zinc-500 font-extrabold uppercase tracking-wider text-[11px]">
              <th class="py-3 pr-4 w-12">#</th>
              <th class="py-3 pr-4">Parlamentar</th>
              <th class="py-3 pr-4">Partido / UF</th>
              <th class="py-3 pr-4 text-center">Assessores</th>
              <th class="py-3 pr-4 text-right">Cota Operacional</th>
              <th class="py-3 pr-4 text-right">Recibos Atípicos</th>
              <th class="py-3 text-right">
                ${selectedModoCusto === 'total' ? 'Custo Total do Gabinete' : 'Total Reembolsado'}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            ${filtered.map((p, idx) => `
              <tr onclick="openStories('${p.nome}')" class="group hover:bg-[#181818] cursor-pointer transition">
                <td class="py-3.5 pr-4 font-mono font-bold text-zinc-500 group-hover:text-[#1ed760]">
                  ${idx + 1}
                </td>
                <td class="py-3.5 pr-4 flex items-center gap-3">
                  <div class="relative shrink-0">
                    <img src="${p.foto || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(p.nome)}" class="w-10 h-10 rounded-full object-cover border border-white/10" alt="${p.nome}" />
                    <div class="absolute inset-0 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 flex items-center justify-center text-[#1ed760] font-black text-xs transition">
                      ▶
                    </div>
                  </div>
                  <div>
                    <div class="flex items-center gap-1.5">
                      <span class="font-extrabold text-sm text-white group-hover:text-[#1ed760] transition">${p.nome}</span>
                      <span class="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${p.is_titular ? 'bg-white/10 text-zinc-300' : 'bg-amber-500/20 text-amber-300'}">
                        ${p.condicao || (p.is_titular ? 'Titular' : 'Suplente')}
                      </span>
                    </div>
                    <div class="text-[11px] text-zinc-500">${p.notas} notas emitidas</div>
                  </div>
                </td>
                <td class="py-3.5 pr-4 font-semibold text-zinc-300">
                  <span class="px-2 py-0.5 rounded bg-white/10 text-xs font-bold text-white mr-1">${p.partido}</span>
                  <span>${p.uf}</span>
                </td>
                <td class="py-3.5 pr-4 text-center font-bold">
                  <span class="px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] font-mono text-zinc-300">
                    👥 ${p.qtd_assessores || 0}
                  </span>
                </td>
                <td class="py-3.5 pr-4 text-right font-mono text-zinc-400">
                  ${fmtBRL(p.total_ceap || p.total)}
                </td>
                <td class="py-3.5 pr-4 text-right font-bold ${p.outliers_z3 > 0 ? 'text-[#ff4632]' : 'text-zinc-600'}">
                  ${p.outliers_z3 > 0 ? `${p.outliers_z3} notas` : '—'}
                </td>
                <td class="py-3.5 text-right font-mono font-black text-sm">
                  <div class="text-[#1ed760]">${fmtBRL(selectedModoCusto === 'total' ? p.custo_total_mandato : p.total)}</div>
                  ${selectedModoCusto === 'total' ? `<div class="text-[10px] text-zinc-500 font-normal">Equipe: ${fmtBRL(p.custo_equipe_ano)}</div>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }

    // STORIES DE GASTOS DO PARLAMENTAR
    function openStories(nome) {
      const match = DATA.parlamentares.find(p => p.nome.toLowerCase() === (nome || '').toLowerCase()) ||
                    DATA.parlamentares.find(p => p.nome.toLowerCase().includes((nome || '').toLowerCase()));
      if (!match) return;

      currentStoryParl = match;
      currentStoryStep = 1;
      renderStorySlide();
      document.getElementById('modal-stories').classList.remove('hidden');
    }

    function closeStories() {
      document.getElementById('modal-stories').classList.add('hidden');
    }

    function nextStory() {
      if (currentStoryStep < 4) {
        currentStoryStep++;
        renderStorySlide();
      } else {
        closeStories();
      }
    }

    function prevStory() {
      if (currentStoryStep > 1) {
        currentStoryStep--;
        renderStorySlide();
      }
    }

    function renderStorySlide() {
      const p = currentStoryParl;
      const wrap = document.getElementById('story-card-wrapper');
      const content = document.getElementById('story-content');
      document.getElementById('story-counter').textContent = `${currentStoryStep} / 4`;

      document.getElementById('prog-1').style.width = currentStoryStep >= 1 ? '100%' : '0%';
      document.getElementById('prog-2').style.width = currentStoryStep >= 2 ? '100%' : '0%';
      document.getElementById('prog-3').style.width = currentStoryStep >= 3 ? '100%' : '0%';
      document.getElementById('prog-4').style.width = currentStoryStep >= 4 ? '100%' : '0%';

      const fallbackFoto = `https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=1ed760&color=000&bold=true`;

      if (currentStoryStep === 1) {
        wrap.className = "relative w-full max-w-md h-[680px] rounded-[32px] overflow-hidden flex flex-col justify-between p-7 shadow-2xl border border-white/20 card-yellow text-black";
        content.innerHTML = `
          <div class="space-y-3.5 my-auto">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-black text-[#f6dc35]">
              1. DOSSIÊ GERAL DO MANDATO
            </span>
            <div class="mx-auto w-24 h-24 rounded-full overflow-hidden border-4 border-black shadow-2xl">
              <img src="${p.foto || fallbackFoto}" onerror="this.src='${fallbackFoto}'" class="w-full h-full object-cover" />
            </div>
            <div>
              <h2 class="text-2xl font-black tracking-tight leading-tight">${p.nome}</h2>
              <p class="text-xs font-bold uppercase tracking-wider opacity-80 mt-0.5">${p.partido} • ${p.uf} • ${p.casa}</p>
            </div>
            
            <div class="py-3 border-y border-black/20 my-2">
              <div class="text-[11px] font-bold uppercase tracking-wider opacity-75">Custo Total Integrado do Mandato (2025)</div>
              <div class="text-3xl font-black tracking-tighter text-black mt-0.5">${fmtBRL(p.custo_total_mandato)}</div>
              <div class="text-[10px] font-extrabold mt-0.5 opacity-80">Soma de Cota + Folha de Gabinete + Salário Oficial</div>
            </div>

            <!-- Os 4 Pilares Financeiros -->
            <div class="grid grid-cols-2 gap-2 text-left text-xs">
              <div class="bg-black/10 p-2.5 rounded-xl border border-black/10">
                <div class="text-[10px] font-bold opacity-75 uppercase">👥 Folha da Equipe</div>
                <div class="text-sm font-black mt-0.5">${fmtBRL(p.custo_equipe_ano)}</div>
                <div class="text-[10px] opacity-75">${p.qtd_assessores || 0} secretários ativos</div>
              </div>
              <div class="bg-black/10 p-2.5 rounded-xl border border-black/10">
                <div class="text-[10px] font-bold opacity-75 uppercase">✈️ Cota Operacional</div>
                <div class="text-sm font-black mt-0.5">${fmtBRL(p.total)}</div>
                <div class="text-[10px] opacity-75">${p.notas} notas fiscais</div>
              </div>
              <div class="bg-black/10 p-2.5 rounded-xl border border-black/10">
                <div class="text-[10px] font-bold opacity-75 uppercase">💰 Salário do Político</div>
                <div class="text-sm font-black mt-0.5">${fmtBRL(p.salario_anual || 602760.47)}</div>
                <div class="text-[10px] opacity-75">Subsídio fixado por lei</div>
              </div>
              <div class="bg-black/10 p-2.5 rounded-xl border border-black/10">
                <div class="text-[10px] font-bold opacity-75 uppercase">🏠 Benefícios</div>
                <div class="text-sm font-black mt-0.5">${fmtBRL(p.auxilio_moradia_ano || 51036.00)}</div>
                <div class="text-[10px] opacity-75">Moradia / Saúde</div>
              </div>
            </div>

            <div class="text-[11px] font-bold opacity-80 pt-1">
              Posição #${p.posicao_nacional} entre todos os 645 políticos do país
            </div>
          </div>
        `;
      } else if (currentStoryStep === 2) {
        wrap.className = "relative w-full max-w-md h-[680px] rounded-[32px] overflow-hidden flex flex-col justify-between p-7 shadow-2xl border border-white/20 bg-gradient-to-br from-[#0f2027] via-[#203a43] to-[#2c5364] text-white";
        const staff = p.assessores || [];
        content.innerHTML = `
          <div class="space-y-3.5 my-auto text-left">
            <div class="text-center">
              <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-[#1ed760] text-black">
                2. A EQUIPE DO GABINETE
              </span>
              <h2 class="text-2xl font-black tracking-tight mt-2">${p.qtd_assessores || 0} Assessores Nomeados</h2>
              <p class="text-xs text-zinc-300 mt-0.5">Folha salarial anual estimada: <span class="font-bold text-[#1ed760] font-mono">${fmtBRL(p.custo_equipe_ano)}</span></p>
            </div>

            <div class="space-y-1.5 max-h-80 overflow-y-auto pr-1">
              ${staff.length > 0 ? staff.map((s, idx) => `
                <div class="p-2.5 rounded-xl bg-black/40 border border-white/10 flex items-center justify-between text-xs">
                  <div class="min-w-0 pr-2">
                    <div class="font-bold text-white truncate">${idx + 1}. ${s.nome}</div>
                    <div class="text-[10px] text-zinc-400 font-mono">${s.cargo || 'Secretário Parlamentar'}</div>
                  </div>
                  <div class="text-right shrink-0">
                    <span class="text-[10px] px-2 py-0.5 rounded bg-white/10 font-bold text-[#1ed760]">
                      Ativo
                    </span>
                  </div>
                </div>
              `).join('') : '<div class="text-xs text-zinc-400 text-center py-6 bg-black/30 rounded-xl">Nenhum assessor comissionado registrado formalmente na data da consulta.</div>'}
            </div>

            <p class="text-[10px] text-zinc-400 text-center">
              Fonte oficial: Tabela de Recursos Humanos da ${p.casa}.
            </p>
          </div>
        `;
      } else if (currentStoryStep === 3) {
        const f = (p.top_fornecedores && p.top_fornecedores[0]) || {};
        wrap.className = "relative w-full max-w-md h-[680px] rounded-[32px] overflow-hidden flex flex-col justify-between p-7 shadow-2xl border border-white/20 card-purple text-white";
        content.innerHTML = `
          <div class="space-y-4 my-auto">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-white text-[#8c52ff]">
              3. FORNECEDOR FAVORITO
            </span>
            <div class="mx-auto w-24 h-24 rounded-2xl overflow-hidden bg-white/20 p-2 border border-white/30 shadow-2xl flex items-center justify-center">
              <img src="${f.logo || 'https://ui-avatars.com/api/?name=EMPRESA'}" class="w-full h-full object-contain" />
            </div>
            <div>
              <div class="text-xs uppercase font-extrabold tracking-wider text-purple-200">Empresa Mais Contratada</div>
              <h2 class="text-2xl font-black tracking-tight leading-tight mt-1">${f.nome || 'Fornecedor'}</h2>
              <p class="text-xs font-mono opacity-80 mt-1">CNPJ: ${f.cnpj || 'Não informado'}</p>
            </div>
            <div class="py-4 border-y border-white/20 my-3 space-y-1">
              <div class="text-xs uppercase font-bold tracking-wider opacity-80">Você contratou essa empresa ${f.notas || 0} vezes, somando</div>
              <div class="text-4xl font-black tracking-tight text-[#1ed760]">${fmtBRL(f.total)}</div>
              <div class="text-sm font-black text-purple-100">${f.share || 0}% de toda a cota do gabinete</div>
            </div>
            <p class="text-xs text-purple-200 max-w-xs mx-auto">
              Esta foi a empresa mais contratada pelo seu mandato no ano inteiro.
            </p>
          </div>
        `;
      } else {
        const atipicas = p.notas_atipicas || [];
        wrap.className = "relative w-full max-w-md h-[680px] rounded-[32px] overflow-hidden flex flex-col justify-between p-7 shadow-2xl border border-white/20 card-orange text-white";
        content.innerHTML = `
          <div class="space-y-4 my-auto">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-black text-[#ff4632]">
              4. AUDITORIA FORENSE
            </span>
            <div>
              <h2 class="text-2xl font-black tracking-tight leading-tight">Notas Fora do Padrão</h2>
              <p class="text-xs font-bold opacity-90 mt-0.5">${p.outliers_z3} recibos com valores acima da mediana nacional (Z-Score > 3)</p>
            </div>
            <div class="space-y-2 text-left max-h-64 overflow-y-auto pr-1">
              ${atipicas.length > 0 ? atipicas.slice(0, 4).map(n => `
                <div onclick='openNotaModal(${JSON.stringify(n).replace(/'/g, "&#39;")})' class="p-3 rounded-2xl bg-black/40 hover:bg-black/60 border border-white/20 cursor-pointer transition">
                  <div class="flex items-center justify-between text-xs font-black">
                    <span class="truncate">${n.fornecedor}</span>
                    <span class="text-[#1ed760] font-mono">${fmtBRL(n.valor)}</span>
                  </div>
                  <div class="text-[11px] opacity-80 mt-0.5">${n.rubrica}</div>
                  <div class="text-[10px] font-bold text-amber-300 mt-1 flex items-center justify-between">
                    <span>${n.multiplo}x a mediana</span>
                    <span class="underline">Ver por que é atípica ↗</span>
                  </div>
                </div>
              `).join('') : '<div class="text-xs font-bold text-center p-4 bg-black/40 rounded-2xl">Parabéns! Todas as notas deste parlamentar estão dentro do padrão normal de mercado.</div>'}
            </div>
            <p class="text-[11px] text-orange-200 text-center">
              Clique em qualquer nota acima para abrir o diagnóstico forense detalhado.
            </p>
          </div>
        `;
      }
    }

    // Modal de Explicação da Nota Atípica
    function openNotaModal(nota) {
      if (!nota || !nota.valor) return;
      const exp = nota.explicacao || {};
      const body = document.getElementById('modal-nota-body');

      body.innerHTML = `
        <div class="space-y-5">
          <div class="flex items-center justify-between border-b border-white/10 pb-3">
            <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-[#ff4632] text-white">
              DIAGNÓSTICO DE AUDITORIA
            </span>
            <span class="text-xs font-mono text-zinc-400">${nota.data || ''}</span>
          </div>

          <div class="bg-[#181818] p-5 rounded-2xl border border-white/5 space-y-1">
            <div class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Valor do Recibo</div>
            <div class="text-4xl font-black text-[#1ed760] font-mono tracking-tight">${fmtBRL(nota.valor)}</div>
            <div class="text-sm font-extrabold text-white pt-2 border-t border-white/10">${nota.fornecedor || 'Fornecedor'}</div>
            <div class="text-xs text-zinc-400 font-mono">CNPJ: ${nota.cnpj || 'Não informado'}</div>
            <div class="text-xs font-bold text-[#8c52ff]">${nota.rubrica || ''}</div>
          </div>

          <div class="bg-[#f6dc35]/10 border border-[#f6dc35]/30 p-4 rounded-2xl space-y-1.5">
            <h4 class="text-xs font-black text-[#f6dc35] uppercase tracking-wider">
              📌 Por que esta nota fiscal está fora do padrão?
            </h4>
            <p class="text-xs text-zinc-200 leading-relaxed font-medium">
              ${exp.resumo_motivo || `Esta nota fiscal de ${fmtBRL(nota.valor)} está muito acima da mediana habitual de ${fmtBRL(nota.mediana || 0)} praticada pelos demais parlamentares.`}
            </p>
          </div>

          <div class="bg-[#181818] border border-white/10 p-4 rounded-2xl space-y-1.5">
            <h4 class="text-xs font-black text-zinc-300 uppercase tracking-wider">
              ⚖️ O que diz a regra oficial?
            </h4>
            <p class="text-xs text-zinc-400 font-mono">${exp.enquadramento_legal || 'Regulamento da Cota Parlamentar'}</p>
            <p class="text-xs text-zinc-300 leading-relaxed">
              ${exp.ponto_atencao || 'Recomenda-se a verificação dos comprovantes materiais de entrega do serviço e compatibilidade de mercado.'}
            </p>
          </div>

          <div class="pt-2">
            ${nota.url ? `
              <a href="${nota.url}" target="_blank" class="w-full py-3.5 px-4 rounded-full text-center text-xs font-black bg-[#1ed760] hover:bg-[#1db954] text-black transition flex items-center justify-center gap-2 shadow-lg">
                📄 Abrir Nota Fiscal Digitalizada na Câmara/Senado ↗
              </a>
            ` : '<div class="text-xs text-zinc-500 text-center font-bold">Link da nota não disponibilizado diretamente pelo portal.</div>'}
          </div>
        </div>
      `;

      document.getElementById('modal-nota').classList.remove('hidden');
    }

    // Buscador
    function searchParl(q) {
      const term = (q || '').toLowerCase().trim();
      const container = document.getElementById('single-parl-card');
      if (!term || term.length < 2) {
        container.innerHTML = '';
        return;
      }

      const matches = DATA.parlamentares.filter(p => p.nome.toLowerCase().includes(term)).slice(0, 4);
      if (matches.length === 0) {
        container.innerHTML = '<div class="text-xs text-[#ff4632] font-bold py-2">Nenhum parlamentar encontrado com esse termo no banco auditado.</div>';
        return;
      }

      let html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3">';
      matches.forEach(match => {
        const fallbackFoto = `https://ui-avatars.com/api/?name=${encodeURIComponent(match.nome)}&background=1ed760&color=000&bold=true`;
        html += `
          <div onclick="openStories('${match.nome}')" class="p-4 rounded-2xl bg-[#181818] border border-white/10 hover:border-[#1ed760] cursor-pointer transition flex items-center justify-between gap-3 group shadow-md hover:bg-[#202020]">
            <div class="flex items-center gap-3.5 min-w-0">
              <img src="${match.foto || fallbackFoto}" onerror="this.src='${fallbackFoto}'" class="w-12 h-12 rounded-full object-cover border-2 border-[#1ed760] shrink-0" alt="${match.nome}" />
              <div class="min-w-0">
                <span class="text-[10px] font-black uppercase tracking-wider text-[#1ed760]">${match.casa === 'Senado Federal' ? 'Senador' : 'Deputado'} • ${match.uf} • <span class="bg-white/10 px-1 py-0.2 rounded text-white">${match.partido}</span></span>
                <h4 class="text-sm font-black text-white mt-0.5 truncate group-hover:text-[#1ed760] transition">${match.nome}</h4>
                <p class="text-[11px] text-zinc-400 mt-0.5 font-mono">${match.notas} notas • ${match.outliers_z3 || 0} atípicas</p>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs font-black text-[#1ed760] font-mono">${fmtBRL(selectedModoCusto === 'total' ? match.custo_total_mandato : match.total)}</div>
              <div class="text-[10px] text-zinc-400 font-mono">${match.qtd_assessores || 0} assessores</div>
              <span class="inline-block mt-1 px-3 py-1 rounded-full bg-white text-black text-[10px] font-black group-hover:bg-[#1ed760] transition">
                Stories ▶
              </span>
            </div>
          </div>
        `;
      });
      html += '</div>';
      container.innerHTML = html;
    }

    initFilters();
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    payload = JSON_PATH.read_text(encoding="utf-8")
    html = HTML_TEMPLATE.replace("__DATA_PAYLOAD__", payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Legislativo Wrapped com Filtro Partidário gerado com sucesso: {OUT_HTML} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
