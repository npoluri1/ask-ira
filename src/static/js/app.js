'use strict';

const STATE = {
  portfolio: JSON.parse(localStorage.getItem('ira_portfolio') || '[]'),
  watchlist: JSON.parse(localStorage.getItem('ira_watchlist') || '[]'),
  alerts: JSON.parse(localStorage.getItem('ira_alerts') || '[]'),
  charts: {},
  currentPage: 'dashboard',
  settings: JSON.parse(localStorage.getItem('ira_settings') || '{}'),
};

const $ = (s, p) => (p || document).querySelector(s);
const $$ = (s, p) => [...((p || document).querySelectorAll(s))];
const fmt = (n, d = 2) => { const v = Number(n); return isNaN(v) ? '0.00' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); };
const fmtUSD = (n) => '$' + fmt(n);
const fmtPct = (n) => (n >= 0 ? '+' : '') + fmt(n, 2) + '%';
const cls = (n) => n >= 0 ? 'up' : 'down';

const CACHE = {
  indices: [],
  movers: { gainers: [], losers: [] },
  news: [],
  forex: [],
  crypto: [],
  commodities: [],
  bonds: [],
};

// ============================================================
// AUTH
// ============================================================
function initAuth() {
  const overlay = $('#loginOverlay');
  const app = $('#app');

  // Tab switching
  $$('.login-tabs .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.login-tabs .tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const form = btn.dataset.ltab === 'register' ? 'registerForm' : 'loginForm';
      $('#loginForm').style.display = form === 'loginForm' ? 'block' : 'none';
      $('#registerForm').style.display = form === 'registerForm' ? 'block' : 'none';
    });
  });

  // Login
  $('#loginBtn').addEventListener('click', async () => {
    const user = $('#loginUser').value.trim();
    const pass = $('#loginPass').value.trim();
    const err = $('#loginError');
    if (!user || !pass) { err.textContent = 'Please fill in all fields'; return; }
    err.textContent = '';
    $('#loginBtn').disabled = true;
    $('#loginBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
    try {
      await API.login(user, pass);
      enterApp();
    } catch (e) {
      err.textContent = e.message;
    }
    $('#loginBtn').disabled = false;
    $('#loginBtn').innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
  });

  // Enter key on login
  $('#loginPass').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('#loginBtn').click(); });

  // Register
  $('#registerBtn').addEventListener('click', async () => {
    const user = $('#regUser').value.trim();
    const pass = $('#regPass').value.trim();
    const email = $('#regEmail').value.trim();
    const err = $('#registerError');
    if (!user || !pass) { err.textContent = 'Please fill in all fields'; return; }
    if (pass.length < 4) { err.textContent = 'Password must be at least 4 characters'; return; }
    err.textContent = '';
    $('#registerBtn').disabled = true;
    $('#registerBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
    try {
      await API.register(user, pass, email);
      enterApp();
    } catch (e) {
      err.textContent = e.message;
    }
    $('#registerBtn').disabled = false;
    $('#registerBtn').innerHTML = '<i class="fas fa-user-plus"></i> Register';
  });

  // Auto-login check
  if (API.isAuthenticated()) {
    API.checkAuth().then(status => {
      if (status.authenticated) {
        enterApp();
      } else {
        API.clearTokens();
        overlay.style.display = 'flex';
        app.style.display = 'none';
      }
    });
  }

  // Listen for forced logout (e.g. 401 from API)
  window.addEventListener('auth:logout', () => {
    API.clearTokens();
    overlay.style.display = 'flex';
    app.style.display = 'none';
  });

  // Logout button in sidebar
  const sidebarFooter = $('.sidebar-footer');
  if (sidebarFooter) {
    const logoutBtn = document.createElement('button');
    logoutBtn.className = 'btn btn-sm';
    logoutBtn.style.width = '100%';
    logoutBtn.style.marginTop = '8px';
    logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
    logoutBtn.addEventListener('click', async () => {
      await API.logout();
      overlay.style.display = 'flex';
      app.style.display = 'none';
      // Reset sidebar nav
      const firstNav = $('.nav-item');
      if (firstNav) { $$('.nav-item').forEach(n => n.classList.remove('active')); firstNav.classList.add('active'); }
      STATE.currentPage = 'dashboard';
    });
    sidebarFooter.appendChild(logoutBtn);
  }

  // Show username in sidebar if logged in
  function updateSidebarUser() {
    const user = API.getUser();
    const statusEl = $('#connStatus');
    if (statusEl && user) {
      statusEl.innerHTML = `<i class="fas fa-user"></i><span>${user.username}</span>`;
    }
  }

  function enterApp() {
    overlay.style.display = 'none';
    app.style.display = 'flex';
    updateSidebarUser();
    // Re-init SSE after login (new token)
    initSSE();
    refreshAll().then(() => {
      renderDashboard();
      renderStocks();
      renderAllIndices();
      renderForex();
      renderCrypto();
      renderCommodities();
      renderBonds();
      renderIPOs();
      renderWatchlist();
      renderAlerts();
      renderScreener();
    });
  }
}

async function refreshAll() {
  const r = await Promise.allSettled([
    API.getIndices().then(d => { if (d?.data) { CACHE.indices = d.data.map(i => ({ name: i.name || i.symbol, symbol: i.symbol, price: i.price, change: i.changePercent, high: i.high, low: i.low, volume: fmt(i.volume, 0), market: 'Global' })); renderTicker(); if (STATE.currentPage === 'dashboard') renderIndices($('#dashMarketFilter')?.value || 'all'); if (STATE.currentPage === 'indices') renderAllIndices($('#indicesFilter')?.value); } }),
    API.getMovers().then(d => { if (d) { CACHE.movers = { gainers: d.gainers || [], losers: d.losers || [] }; if (STATE.currentPage === 'dashboard') renderMovers(document.querySelector('.tab-btn[data-mover].active')?.dataset.mover || 'gainers'); } }),
    API.getNews().then(d => { if (d?.data) { CACHE.news = d.data; if (STATE.currentPage === 'dashboard') renderNews(); } }),
    API.getForex().then(d => { if (d?.data) { CACHE.forex = d.data; if (STATE.currentPage === 'forex') renderForex($('#forexFilter')?.value); } }),
    API.getCrypto().then(d => { if (d?.data) { CACHE.crypto = d.data; if (STATE.currentPage === 'crypto') renderCrypto(); } }),
    API.getCommodities().then(d => { if (d?.data) { CACHE.commodities = d.data; if (STATE.currentPage === 'commodities') renderCommodities(); } }),
    API.getBonds().then(d => { if (d?.data) { CACHE.bonds = d.data; if (STATE.currentPage === 'bonds') renderBonds(); } }),
  ]);
}

function initNav() {
  $$('.nav-item').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const page = el.dataset.page;
      if (!page) return;
      $$('.nav-item').forEach(n => n.classList.remove('active'));
      el.classList.add('active');
      $$('.page').forEach(p => p.classList.remove('active'));
      const target = document.getElementById(`page-${page}`);
      if (target) target.classList.add('active');
      STATE.currentPage = page;
      if (window.innerWidth <= 768) $('#sidebar').classList.remove('open');
      renderPage(page);
    });
  });
  $('#menuToggle')?.addEventListener('click', () => { $('#sidebar').classList.toggle('open'); });
}

function initMobile() {
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && $('#sidebar').classList.contains('open') && !$('#sidebar').contains(e.target) && !$('#menuToggle')?.contains(e.target)) $('#sidebar').classList.remove('open');
  });
  window.addEventListener('resize', () => { if (window.innerWidth > 768) $('#sidebar').classList.remove('open'); });
}

let sseSource = null;
function initSSE() {
  if (sseSource) { sseSource.close(); }
  sseSource = new EventSource('/api/v1/market/live');
  sseSource.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case 'indices':
          CACHE.indices = (msg.data || []).map(i => ({ name: i.name || i.symbol, symbol: i.symbol, price: i.price, change: i.changePercent, high: i.high, low: i.low, volume: fmt(i.volume, 0), market: 'Global' }));
          renderTicker();
          if (STATE.currentPage === 'dashboard') renderIndices($('#dashMarketFilter')?.value || 'all');
          if (STATE.currentPage === 'indices') renderAllIndices($('#indicesFilter')?.value);
          break;
        case 'stocks':
          CACHE.stocks = msg.data || [];
          if (STATE.currentPage === 'stocks') renderStocks();
          if (STATE.currentPage === 'screener') renderScreener();
          break;
        case 'forex':
          CACHE.forex = msg.data || [];
          if (STATE.currentPage === 'forex') renderForex($('#forexFilter')?.value);
          break;
        case 'crypto':
          CACHE.crypto = msg.data || [];
          if (STATE.currentPage === 'crypto') renderCrypto();
          break;
        case 'news':
          CACHE.news = msg.data || [];
          if (STATE.currentPage === 'dashboard') renderNews();
          break;
        case 'insights':
          if (msg.data) {
            Object.entries(msg.data).forEach(([section, insight]) => {
              const key = `_ai_insight_${section}`;
              CACHE[key] = { insight, confidence: 0.8, updatedAt: msg.updatedAt };
              if (STATE.currentPage === section) {
                renderAIInsightFromCache(section, insight, msg.updatedAt);
              }
            });
          }
          break;
      }
    } catch(e) {}
  };
  sseSource.onerror = () => {
    sseSource.close();
    setTimeout(initSSE, 5000);
  };
}

function updateClock() {
  $('#clock').textContent = new Date().toLocaleString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short' });
}

function renderTicker() {
  const t = $('#marketTicker');
  if (!t || CACHE.indices.length === 0) return;
  t.innerHTML = CACHE.indices.slice(0, 8).map(i => `<div class="ticker-item ${cls(i.change)}"><span class="ticker-sym">${i.symbol}</span><span class="ticker-val">${fmt(i.price, i.price < 100 ? 4 : 2)}</span><span class="ticker-chg">${fmtPct(i.change)}</span></div>`).join('');
}

$('#refreshBtn')?.addEventListener('click', () => {
  $('#refreshBtn i').classList.add('fa-spin');
  refreshAll().finally(() => setTimeout(() => $('#refreshBtn i').classList.remove('fa-spin'), 500));
});

function renderPage(page) {
  updateDataSourceUI();
  startAIRefresh(page);
  switch (page) {
    case 'dashboard': renderDashboard(); showAIInsight('dashboard', 'ai-dashboard'); break;
    case 'stocks': renderStocks(); showAIInsight('stocks', 'ai-stocks'); break;
    case 'indices': renderAllIndices(); showAIInsight('indices', 'ai-indices'); break;
    case 'forex': renderForex(); showAIInsight('forex', 'ai-forex'); break;
    case 'crypto': renderCrypto(); showAIInsight('crypto', 'ai-crypto'); break;
    case 'commodities': renderCommodities(); showAIInsight('commodities', 'ai-commodities'); break;
    case 'bonds': renderBonds(); showAIInsight('bonds', 'ai-bonds'); break;
    case 'options': showAIInsight('options', 'ai-options'); break;
    case 'funds': renderFunds(); showAIInsight('funds', 'ai-funds'); break;
    case 'ipos': renderIPOs(); break;
    case 'watchlist': renderWatchlist(); break;
    case 'portfolio': renderPortfolio(); break;
    case 'screener': renderScreener(); break;
    case 'alerts': renderAlerts(); break;
    case 'settings': break;
    case 'banking': renderBanking(); break;
    case 'payments': renderPayments(); break;
    case 'wallets': renderWallets(); break;
    case 'insurance': renderInsurance(); break;
    case 'compliance': renderCompliance(); break;
    case 'security': renderSecurity(); break;
  }
}

function renderDashboard() {
  renderIndices($('#dashMarketFilter')?.value || 'all');
  renderMovers(document.querySelector('.tab-btn[data-mover].active')?.dataset.mover || 'gainers');
  renderNews();
  renderEconCalendar();
  renderMarketChart();
}

function renderIndices(filter) {
  const grid = $('#indicesGrid');
  if (!grid) return;
  const items = filter && filter !== 'all' ? CACHE.indices.filter(i => i.market === filter) : CACHE.indices;
  if (items.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = items.map(i => `<div class="indice-card"><div class="indice-header"><span class="indice-name">${i.symbol}</span><span class="indice-flag">${i.name}</span></div><div class="indice-price">${fmtUSD(i.price)}</div><div class="indice-change ${cls(i.change)}"><i class="fas fa-${i.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(i.change)}</div><div class="indice-detail"><span>H: ${fmtUSD(i.high)}</span><span>L: ${fmtUSD(i.low)}</span><span>Vol: ${i.volume}</span></div></div>`).join('');
}
$('#dashMarketFilter')?.addEventListener('change', (e) => renderIndices(e.target.value));

function renderMovers(type) {
  const c = $('#moversList'); if (!c) return;
  const items = CACHE.movers[type] || [];
  if (items.length === 0) { c.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  c.innerHTML = items.map(m => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${m.symbol}</span><span class="mover-price">${fmtUSD(m.price)}</span></div><span class="mover-change ${cls(m.changePercent)}">${fmtPct(m.changePercent)}</span></div>`).join('');
}
$$('.tab-btn[data-mover]').forEach(b => b.addEventListener('click', () => { $$('.tab-btn[data-mover]').forEach(x => x.classList.remove('active')); b.classList.add('active'); renderMovers(b.dataset.mover); }));

function renderNews() {
  const l = $('#newsList'); if (!l) return;
  if (CACHE.news.length === 0) { l.innerHTML = '<div class="loader" style="height:80px"></div>'; return; }
  l.innerHTML = CACHE.news.slice(0, 8).map(n => `<div class="news-item"><div class="news-title">${n.title}</div><div class="news-meta"><span class="news-source">${n.source}</span><span>${n.timestamp ? new Date(n.timestamp * 1000).toLocaleDateString() : ''}</span></div></div>`).join('');
}

function renderEconCalendar() {
  const c = $('#econCalendar'); if (!c) return;
  c.innerHTML = [
    { event: 'Fed Interest Rate Decision', date: 'Jun 2025', importance: 'high' },
    { event: 'US CPI (May)', date: 'Weekly', importance: 'high' },
    { event: 'US Nonfarm Payrolls', date: 'Monthly', importance: 'high' },
  ].map(e => `<div class="econ-item"><div><span class="econ-event">${e.event}</span>${e.importance === 'high' ? '<span class="econ-important">HIGH</span>' : ''}</div><div class="econ-forecast">${e.date}</div></div>`).join('');
}

function renderMarketChart() {
  const canvas = $('#marketChart'); if (!canvas) return;
  if (STATE.charts.market) STATE.charts.market.destroy();
  if (CACHE.indices.length < 3) return;
  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  STATE.charts.market = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: CACHE.indices.slice(0, 3).map((i, idx) => ({ label: i.symbol, data: labels.map(() => i.price * (1 + (Math.random() - 0.5) * 0.06)), borderColor: ['#3b82f6', '#22c55e', '#eab308'][idx], tension: 0.3, fill: false })) },
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0', font: { size: 11 } } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 10 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

function renderStocks() {
  const cont = $('#trendingStocks');
  if (!cont) return;
  const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM'];
  if (CACHE.indices.length === 0) { cont.innerHTML = '<div class="loader" style="height:120px"></div>'; }
  API.getStocks().then(d => {
    if (!d?.data) return;
    cont.innerHTML = d.data.map(s => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${s.symbol}</span><span class="mover-price">${fmtUSD(s.price)}</span></div><span class="mover-change ${cls(s.changePercent)}">${fmtPct(s.changePercent)}</span></div>`).join('');
  });
  renderSectorChart();
}

function renderSectorChart() {
  const canvas = $('#sectorChart'); if (!canvas) return;
  if (STATE.charts.sector) STATE.charts.sector.destroy();
  const sectors = ['Technology', 'Banking', 'Automotive', 'Energy', 'Healthcare', 'Consumer', 'IT Services'];
  STATE.charts.sector = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels: sectors, datasets: [{ label: 'Sector Performance (%)', data: sectors.map(() => (Math.random() - 0.3) * 8), backgroundColor: sectors.map(() => '#3b82f680'), borderColor: '#3b82f6', borderWidth: 1 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 10 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

function initStockSearch() {
  $('#stockSearchBtn')?.addEventListener('click', doStockSearch);
  $('#stockQuery')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') doStockSearch(); });
  $$('.chip[data-stock]').forEach(c => c.addEventListener('click', () => { $('#stockQuery').value = c.dataset.stock; doStockSearch(); }));
}

async function doStockSearch() {
  const q = $('#stockQuery')?.value.trim(); if (!q) return;
  const results = $('#stockResults'); results.style.display = 'block';
  results.innerHTML = '<div class="loader" style="height:200px"></div>';
  try {
    const d = await API.query({ query: `Provide detailed analysis of ${q} stock with financials, technicals, and outlook`, session_id: 'stock_' + Date.now() });
    results.innerHTML = `<div class="card"><div class="card-header"><h3><i class="fas fa-chart-bar"></i> ${q.toUpperCase()} Analysis</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(d.report || d.analysis || 'No data')}</div></div></div>`;
  } catch (e) { results.innerHTML = `<div class="context-box error">${e.message}</div>`; }
}

function renderAllIndices(filter) {
  const grid = $('#allIndicesGrid'); if (!grid) return;
  const items = filter && filter !== 'all' ? CACHE.indices.filter(i => i.region === filter) : CACHE.indices;
  if (items.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = items.map(i => `<div class="indice-card"><div class="indice-header"><span class="indice-name">${i.symbol}</span><span class="indice-flag">${i.name}</span></div><div class="indice-price">${fmtUSD(i.price)}</div><div class="indice-change ${cls(i.change)}"><i class="fas fa-${i.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(i.change)}</div><div class="indice-detail"><span>H: ${fmtUSD(i.high)}</span><span>L: ${fmtUSD(i.low)}</span></div></div>`).join('');
  renderIndicesComparisonChart();
}
$('#indicesFilter')?.addEventListener('change', (e) => renderAllIndices(e.target.value));

function renderIndicesComparisonChart() {
  const canvas = $('#indicesChart'); if (!canvas) return;
  if (STATE.charts.indices) STATE.charts.indices.destroy();
  if (CACHE.indices.length === 0) return;
  STATE.charts.indices = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels: CACHE.indices.map(i => i.symbol), datasets: [{ label: 'Change (%)', data: CACHE.indices.map(i => i.change), backgroundColor: CACHE.indices.map(i => i.change >= 0 ? '#22c55e80' : '#ef444480'), borderColor: CACHE.indices.map(i => i.change >= 0 ? '#22c55e' : '#ef4444'), borderWidth: 1 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 9 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

function renderForex(filter) {
  const grid = $('#forexGrid'); if (!grid) return;
  const items = filter && filter !== 'all' ? CACHE.forex.filter(f => f.type === filter) : CACHE.forex;
  if (items.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = items.map(f => `<div class="forex-card"><div class="fx-pair">${f.symbol}</div><div class="fx-rate">${fmt(f.price, f.price < 10 ? 4 : 2)}</div><div class="fx-change ${cls(f.changePercent)}"><i class="fas fa-${f.changePercent >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(f.changePercent)}</div></div>`).join('');
  renderForexChart();
}
$('#forexFilter')?.addEventListener('change', (e) => renderForex(e.target.value));

function renderForexChart() {
  const canvas = $('#forexChart'); if (!canvas) return;
  if (STATE.charts.forex) STATE.charts.forex.destroy();
  const labels = Array.from({ length: 20 }, (_, i) => `Day ${i + 1}`);
  STATE.charts.forex = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [{ label: 'EUR/USD', data: labels.map(() => CACHE.forex[0]?.price * (1 + (Math.random() - 0.5) * 0.02) || 1.08), borderColor: '#3b82f6', tension: 0.3, fill: false }] },
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0' } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

function renderCrypto() {
  const grid = $('#cryptoGrid'); if (!grid) return;
  if (CACHE.crypto.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = CACHE.crypto.slice(0, 8).map(c => `<div class="crypto-card"><div class="crypto-name">${c.symbol} <span style="color:var(--text-muted);font-size:12px">${c.symbol}</span></div><div class="crypto-price">${fmtUSD(c.price)}</div><div class="crypto-change ${cls(c.changePercent)}">${fmtPct(c.changePercent)}</div></div>`).join('');
  renderCryptoChart();
}

function renderCryptoChart() {
  const canvas = $('#cryptoChart'); if (!canvas) return;
  if (STATE.charts.crypto) STATE.charts.crypto.destroy();
  const labels = Array.from({ length: 30 }, (_, i) => `D${i + 1}`);
  STATE.charts.crypto = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: CACHE.crypto.slice(0, 2).map((c, i) => ({ label: c.symbol, data: labels.map(() => c.price * (1 + (Math.random() - 0.5) * 0.05)), borderColor: ['#f7931a', '#627eea'][i], tension: 0.3 })) },
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0', font: { size: 11 } } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 9 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

function renderCommodities() {
  const grid = $('#commoditiesGrid'); if (!grid) return;
  if (CACHE.commodities.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = CACHE.commodities.map(c => `<div class="commodity-card"><div class="crypto-name">${c.symbol} <span style="color:var(--text-muted);font-size:12px">${c.symbol}</span></div><div class="crypto-price">${fmtUSD(c.price)}</div><div class="crypto-change ${cls(c.changePercent)}">${fmtPct(c.changePercent)}</div></div>`).join('');
}

function renderBonds() {
  const grid = $('#bondsGrid'); if (!grid) return;
  if (CACHE.bonds.length === 0) { grid.innerHTML = '<div class="loader" style="height:120px"></div>'; return; }
  grid.innerHTML = CACHE.bonds.map(b => `<div class="bond-card"><div class="crypto-name">${b.symbol} <span style="color:var(--text-muted);font-size:12px">${b.symbol}</span></div><div class="crypto-price">${fmt(b.yield || b.price, 2)}%</div><div class="crypto-change ${cls(-(b.changePercent || b.change || 0))}"><i class="fas fa-${(b.changePercent || b.change || 0) >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(b.changePercent || b.change || 0)}</div></div>`).join('');
}

function renderIPOs() {
  const grid = $('#iposGrid'); if (!grid) return;
  const ipos = [
    { name: 'Stripe Inc.', symbol: 'STRIPE', exchange: 'NYSE', date: 'TBD', type: 'Tech', status: 'upcoming' },
    { name: 'Reddit', symbol: 'RDDT', exchange: 'NYSE', price: 58.45, date: '2024', type: 'Tech', status: 'listed', change: 18.5 },
    { name: 'Arm Holdings', symbol: 'ARM', exchange: 'NASDAQ', price: 124.80, date: '2023', type: 'Semicon', status: 'listed', change: 112.4 },
  ];
  grid.innerHTML = ipos.map(ipo => `<div class="ipo-card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span class="crypto-name">${ipo.name}</span><span class="badge-lg" style="${ipo.status === 'listed' ? 'color:var(--up);background:rgba(34,197,94,0.1)' : 'color:var(--accent-yellow);background:rgba(234,179,8,0.1)'}">${ipo.status.toUpperCase()}</span></div><div style="font-size:12px;color:var(--text-muted)">${ipo.exchange} · ${ipo.type} · ${ipo.date}</div><div style="margin-top:6px;font-size:14px;font-weight:600">${ipo.status === 'listed' ? fmtUSD(ipo.price) + (ipo.change ? ` <span class="${cls(ipo.change)}">${fmtPct(ipo.change)}</span>` : '') : 'Pricing TBD'}</div></div>`).join('');
}

function renderFunds() {
  const popular = $('#popularFunds');
  if (!popular) return;
  popular.innerHTML = '<div class="loader"></div>';
  setTimeout(() => {
    popular.innerHTML = `<div style="padding:16px;font-size:13px;color:var(--text-secondary)">Search for funds above or use the AI Research page for personalized fund recommendations. Popular categories: ETFs, Index Funds, Mutual Funds.</div>`;
  }, 500);
}

function initResearch() {
  $('#researchBtn')?.addEventListener('click', doResearch);
  $('#researchQuery')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') doResearch(); });
  $$('.chip[data-q]').forEach(c => c.addEventListener('click', () => { $('#researchQuery').value = c.dataset.q; doResearch(); }));
  $$('.r-tab').forEach(t => t.addEventListener('click', () => {
    $$('.r-tab').forEach(x => x.classList.remove('active')); t.classList.add('active');
    const active = $('#researchContent')?.querySelector(`[data-rtab-content="${t.dataset.rtab}"]`);
    if (active) { $$('#researchContent > div').forEach(d => d.style.display = 'none'); active.style.display = 'block'; }
  }));
}

async function doResearch() {
  const query = $('#researchQuery')?.value.trim(); if (!query) return;
  const btn = $('#researchBtn'); const results = $('#researchResults'); const content = $('#researchContent');
  btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Researching...';
  results.style.display = 'block'; content.innerHTML = '<div class="loader" style="height:200px"></div>';
  try {
    const data = await API.query({ query, session_id: 'ui_' + Date.now(), risk_profile: 'moderate' });
    const tabs = ['report', 'analysis', 'mcp', 'portfolio', 'risk'];
    content.innerHTML = tabs.map(t => `<div data-rtab-content="${t}" style="display:${t === 'report' ? 'block' : 'none'}">${t === 'report' ? `<div class="context-box info"><strong>Query:</strong> ${query}</div><div class="markdown-body">${mdToHtml(data.report || '')}</div>` : t === 'analysis' ? `<div class="markdown-body">${mdToHtml(data.analysis || 'No analysis')}</div>${data.confidence ? `<div style="margin-top:16px;padding:12px 16px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:3px solid #3b82f6"><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(0)}%</div>` : ''}` : t === 'mcp' ? `<div class="mcp-grid">${Object.entries(data.mcp_results || {}).map(([k, v]) => `<div class="mcp-item"><h4>${k}</h4><p>${v}</p></div>`).join('')}</div>` : t === 'portfolio' ? (data.portfolio_allocation ? `<div class="context-box success"><strong>Risk Profile:</strong> ${data.portfolio_allocation.risk_profile}</div><div class="mcp-grid">${Object.entries(data.portfolio_allocation.allocation || {}).map(([k, v]) => `<div class="mcp-item"><h4>${k}</h4><p style="font-size:18px;font-weight:700">${(v * 100).toFixed(0)}%</p></div>`).join('')}</div><div style="margin-top:16px;font-size:13px;color:var(--text-secondary)">${data.portfolio_allocation.recommendation || ''}</div>` : '<p>No data</p>') : t === 'risk' ? (data.risk_assessment ? `<div class="markdown-body">${mdToHtml(typeof data.risk_assessment === 'string' ? data.risk_assessment : JSON.stringify(data.risk_assessment, null, 2))}</div>` : '<p>No data</p>') : ''}</div>`).join('');
  } catch (err) { content.innerHTML = `<div class="context-box error"><strong>Error:</strong> ${err.message}</div>`; }
  btn.disabled = false; btn.innerHTML = '<i class="fas fa-robot"></i> Research';
}

function mdToHtml(md) {
  if (!md) return '';
  return md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/^### (.+)$/gm, '<h4>$1</h4>').replace(/^## (.+)$/gm, '<h3>$1</h3>').replace(/^# (.+)$/gm, '<h2>$1</h2>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
}

function renderPortfolio() {
  const h = STATE.portfolio; const tv = h.reduce((s, x) => s + x.qty * (x.currentPrice || x.cost), 0);
  const tc = h.reduce((s, x) => s + x.qty * x.cost, 0); const tp = tv - tc;
  const ret = tc > 0 ? (tp / tc) * 100 : 0;
  $('#portfolioSummary').innerHTML = `
    <div class="summary-card"><span class="summary-label">Total Value</span><span class="summary-value">${fmtUSD(tv)}</span></div>
    <div class="summary-card"><span class="summary-label">Total P&L</span><span class="summary-value ${cls(tp)}">${tp >= 0 ? '+' : ''}${fmtUSD(tp)}</span></div>
    <div class="summary-card"><span class="summary-label">Returns</span><span class="summary-value ${cls(ret)}">${fmtPct(ret)}</span></div>`;
  const body = $('#holdingsBody');
  if (h.length === 0) body.innerHTML = '<tr><td colspan="8" class="text-center">No holdings yet.</td></tr>';
  else body.innerHTML = h.map((x, i) => { const mv = x.qty * (x.currentPrice || x.cost); const pnl = (x.currentPrice || x.cost) - x.cost; const pp = x.cost > 0 ? (pnl / x.cost) * 100 : 0; return `<tr><td><strong>${x.ticker}</strong></td><td>${x.qty}</td><td>${fmtUSD(x.cost)}</td><td>${fmtUSD(x.currentPrice || x.cost)}</td><td>${fmtUSD(mv)}</td><td class="${cls(pnl)}">${fmtUSD(pnl * x.qty)}</td><td class="${cls(pp)}">${fmtPct(pp)}</td><td><button class="btn btn-sm" onclick="removeHolding(${i})"><i class="fas fa-trash"></i></button></td></tr>`; }).join('');
  renderAllocationChart(h);
}

function renderAllocationChart(holdings) {
  const canvas = $('#allocationChart'); if (!canvas) return;
  if (STATE.charts.allocation) STATE.charts.allocation.destroy();
  if (holdings.length === 0) return;
  const byType = {}; holdings.forEach(x => { byType[x.type || 'stock'] = (byType[x.type || 'stock'] || 0) + x.qty * (x.currentPrice || x.cost); });
  STATE.charts.allocation = new Chart(canvas.getContext('2d'), { type: 'doughnut', data: { labels: Object.keys(byType), datasets: [{ data: Object.values(byType), backgroundColor: ['#3b82f6', '#22c55e', '#eab308', '#a855f7', '#06b6d4'] }] }, options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#9aa0b0', font: { size: 11 } } } } } });
}

function addHolding(t, type, qty, cost, market) {
  STATE.portfolio.push({ ticker: t.toUpperCase(), type: type || 'stock', qty: Number(qty) || 1, cost: Number(cost) || 0, market: market || 'US', currentPrice: Number(cost) * (1 + (Math.random() - 0.5) * 0.1), addedAt: new Date().toISOString() });
  localStorage.setItem('ira_portfolio', JSON.stringify(STATE.portfolio)); renderPortfolio();
}
window.removeHolding = (i) => { STATE.portfolio.splice(i, 1); localStorage.setItem('ira_portfolio', JSON.stringify(STATE.portfolio)); renderPortfolio(); };

function initPortfolio() {
  $('#addHoldingBtn')?.addEventListener('click', () => $('#holdingModal').classList.add('show'));
  $('.modal-close')?.addEventListener('click', () => { $$('.modal.show').forEach(m => m.classList.remove('show')); });
  $('#cancelHolding')?.addEventListener('click', () => $('#holdingModal').classList.remove('show'));
  $('#saveHolding')?.addEventListener('click', () => {
    const t = $('#holdingTicker').value.trim(); if (!t) return;
    addHolding(t, $('#holdingType').value, $('#holdingQty').value, $('#holdingCost').value, $('#holdingMarket').value);
    $('#holdingModal').classList.remove('show'); $('#holdingTicker').value = ''; $('#holdingQty').value = '1'; $('#holdingCost').value = '';
  });
  $('#holdingModal')?.addEventListener('click', (e) => { if (e.target === $('#holdingModal')) $('#holdingModal').classList.remove('show'); });
}

function renderWatchlist() {
  const body = $('#watchlistBody'); const w = STATE.watchlist;
  if (w.length === 0) body.innerHTML = '<p class="text-center">Your watchlist is empty.</p>';
  else body.innerHTML = w.map((x, i) => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${x.ticker}</span><span class="mover-price">${x.market || 'US'}</span></div><button class="btn btn-sm" onclick="removeWatch(${i})"><i class="fas fa-times"></i></button></div>`).join('');
}
function addWatch(ticker, market) {
  STATE.watchlist.push({ ticker: ticker.toUpperCase(), market: market || 'US', addedAt: new Date().toISOString() });
  localStorage.setItem('ira_watchlist', JSON.stringify(STATE.watchlist)); renderWatchlist();
}
window.removeWatch = (i) => { STATE.watchlist.splice(i, 1); localStorage.setItem('ira_watchlist', JSON.stringify(STATE.watchlist)); renderWatchlist(); };

function initWatchlist() {
  $('#addWatchBtn')?.addEventListener('click', () => $('#watchModal').classList.add('show'));
  $('#cancelWatch')?.addEventListener('click', () => $('#watchModal').classList.remove('show'));
  $('#saveWatch')?.addEventListener('click', () => {
    const t = $('#watchTicker').value.trim(); if (!t) return;
    addWatch(t, $('#watchMarket').value);
    $('#watchModal').classList.remove('show'); $('#watchTicker').value = '';
  });
  $('#watchModal')?.addEventListener('click', (e) => { if (e.target === $('#watchModal')) $('#watchModal').classList.remove('show'); });
}

function renderScreener() {
  const cont = $('#screenerResults'); if (!cont) return;
  const stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'JNJ'];
  cont.innerHTML = `<div style="overflow-x:auto"><table class="screener-table"><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Mkt Cap</th><th>P/E</th><th>Volume</th></tr></thead><tbody>${stocks.map(s => `<tr><td><strong>${s}</strong></td><td class="screener-loading" colspan="5"><i class="fas fa-spinner fa-spin"></i></td></tr>`).join('')}</tbody></table></div>`;
  API.getStocks().then(d => {
    if (!d?.data) return;
    cont.innerHTML = `<div style="overflow-x:auto"><table class="screener-table"><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>High</th><th>Low</th><th>Volume</th></tr></thead><tbody>${d.data.map(s => `<tr><td><strong>${s.symbol}</strong></td><td>${fmtUSD(s.price)}</td><td class="${cls(s.changePercent)}">${fmtPct(s.changePercent)}</td><td>${fmtUSD(s.high)}</td><td>${fmtUSD(s.low)}</td><td>${fmt(s.volume, 0)}</td></tr>`).join('')}</tbody></table></div>`;
  });
}
$('#screenerBtn')?.addEventListener('click', () => renderScreener());

$('#optionsSearchBtn')?.addEventListener('click', async () => {
  const t = $('#optionsTicker')?.value.trim().toUpperCase(); if (!t) return;
  const type = $('#optionsType')?.value || 'options';
  const cont = $('#optionsResults');
  cont.innerHTML = `<div class="card"><div class="card-header"><h3>${t} ${type.toUpperCase()}</h3></div><div class="card-body"><div class="loader"></div></div></div>`;
  try {
    const data = await API.query({ query: `Show ${type} chain and analysis for ${t}`, session_id: 'opt_' + Date.now() });
    cont.innerHTML = `<div class="card"><div class="card-header"><h3>${t} ${type.toUpperCase()}</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(data.report || data.analysis || 'No data')}</div></div></div>`;
  } catch (e) { cont.innerHTML = `<div class="context-box error">${e.message}</div>`; }
});

function initCompare() {
  $('#compareBtn')?.addEventListener('click', async () => {
    const t1 = $('#compTicker1').value.trim().toUpperCase(); const t2 = $('#compTicker2').value.trim().toUpperCase();
    const t3 = $('#compTicker3').value.trim().toUpperCase(); if (!t1 || !t2) return;
    const r = $('#comparisonResults'); r.style.display = 'block'; r.innerHTML = '<div class="loader" style="height:200px"></div>';
    try {
      const q = `Compare ${t1} vs ${t2}${t3 ? ' vs ' + t3 : ''} across financial metrics, valuation, growth, and risks`;
      const d = await API.query({ query: q, session_id: 'cmp_' + Date.now() });
      r.innerHTML = `<div class="card"><div class="card-header"><h3><i class="fas fa-balance-scale"></i> ${t1} vs ${t2}${t3 ? ' vs ' + t3 : ''}</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(d.report || d.analysis || 'No data')}</div></div></div>`;
    } catch (e) { r.innerHTML = `<div class="context-box error">${e.message}</div>`; }
  });
}

function initRisk() {
  $('#riskBtn')?.addEventListener('click', async () => {
    const t = $('#riskTicker').value.trim().toUpperCase(); const p = $('#riskProfile').value; if (!t) return;
    const r = $('#riskResults'); r.style.display = 'block'; r.innerHTML = '<div class="loader" style="height:200px"></div>';
    try {
      const d = await API.query({ query: `Detailed risk assessment for ${t} with ${p} profile`, session_id: 'risk_' + Date.now(), risk_profile: p });
      r.innerHTML = `<div class="card"><div class="card-header"><h3><i class="fas fa-shield-alt"></i> Risk: ${t}</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(d.risk_assessment || d.analysis || d.report || 'No data')}</div></div></div>`;
    } catch (e) { r.innerHTML = `<div class="context-box error">${e.message}</div>`; }
  });
}

function renderAlerts() {
  const c = $('#alertsList'); const a = STATE.alerts;
  if (a.length === 0) c.innerHTML = '<p class="text-center">No alerts set.</p>';
  else c.innerHTML = a.map((x, i) => `<div class="alert-item"><div class="alert-info"><span class="alert-ticker">${x.ticker}</span> ${x.condition === 'above' ? '>' : x.condition === 'below' ? '<' : '±'} ${x.value}</div><button class="alert-remove" onclick="removeAlert(${i})"><i class="fas fa-trash"></i></button></div>`).join('');
}
function addAlert(ticker, condition, value) {
  STATE.alerts.push({ ticker: ticker.toUpperCase(), condition, value: Number(value), createdAt: new Date().toISOString() });
  localStorage.setItem('ira_alerts', JSON.stringify(STATE.alerts)); renderAlerts(); updateAlertBadge();
}
window.removeAlert = (i) => { STATE.alerts.splice(i, 1); localStorage.setItem('ira_alerts', JSON.stringify(STATE.alerts)); renderAlerts(); updateAlertBadge(); };
function updateAlertBadge() { const b = $('#alertBadge'); if (b) b.textContent = STATE.alerts.length; }

function initAlerts() {
  $('#addAlertBtn')?.addEventListener('click', () => $('#alertModal').classList.add('show'));
  $('#cancelAlert')?.addEventListener('click', () => $('#alertModal').classList.remove('show'));
  $('#saveAlert')?.addEventListener('click', () => {
    const t = $('#alertTicker').value.trim(); if (!t) return;
    addAlert(t, $('#alertCondition').value, $('#alertValue').value);
    $('#alertModal').classList.remove('show'); $('#alertTicker').value = ''; $('#alertValue').value = '';
  });
  $('#alertModal')?.addEventListener('click', (e) => { if (e.target === $('#alertModal')) $('#alertModal').classList.remove('show'); });
  updateAlertBadge();
}

function updateDataSourceUI() {
  API.getDataSource().then(d => {
    if (!d) return;
    const badge = $('#dataSourceBadge');
    const sBadge = $('#settingsBadge');
    const sLabel = $('#settingsDataSourceLabel');
    if (badge) {
      badge.textContent = d.badge?.label || 'AI';
      badge.style.color = d.badge?.color || 'var(--accent-cyan)';
      badge.style.background = d.badge?.bg || 'rgba(6,182,212,0.15)';
    }
    if (sBadge) {
      sBadge.textContent = d.badge?.label || 'AI';
      sBadge.style.color = d.badge?.color || 'var(--accent-cyan)';
      sBadge.style.background = d.badge?.bg || 'rgba(6,182,212,0.15)';
    }
    if (sLabel) sLabel.textContent = d.label || 'AI-Generated Market Data';
  });
}

function initSettings() {
  const saved = STATE.settings.provider || 'openai';
  $('#settingsProvider').value = saved;
  if (STATE.settings.apiKey) $('#settingsApiKey').value = STATE.settings.apiKey;
  $('#saveSettings')?.addEventListener('click', () => {
    STATE.settings.provider = $('#settingsProvider').value;
    STATE.settings.apiKey = $('#settingsApiKey').value;
    localStorage.setItem('ira_settings', JSON.stringify(STATE.settings));
    const status = $('#settingsStatus');
    status.textContent = '✓ Settings saved! Using ' + $('#settingsProvider').options[$('#settingsProvider').selectedIndex].text;
    setTimeout(() => status.textContent = '', 3000);
  });
  updateDataSourceUI();
  $('#toggleDataSourceBtn')?.addEventListener('click', async () => {
    const btn = $('#toggleDataSourceBtn'); btn.disabled = true;
    try {
      await API.toggleDataSource();
      updateDataSourceUI();
      const status = $('#settingsDsStatus');
      status.textContent = '✓ Data source toggled! Refreshing data...';
      setTimeout(() => status.textContent = '', 3000);
      CACHE._refreshed = 0;
      renderPage(currentPage);
    } catch (e) {
      alert('Toggle failed: ' + e.message);
    }
    btn.disabled = false;
  });
}

$$('.modal .modal-close').forEach(b => b.addEventListener('click', () => { b.closest('.modal').classList.remove('show'); }));

function initFundSearch() {
  $('#fundSearchBtn')?.addEventListener('click', async () => {
    const q = $('#fundQuery')?.value.trim() || 'best performing funds';
    const t = $('#fundType')?.value || 'all'; const m = $('#fundMarket')?.value || 'US';
    const btn = $('#fundSearchBtn'); btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    try {
      const d = await API.query({ query: `${q} in ${m} market, type: ${t}`, session_id: 'funds_' + Date.now() });
      const grid = $('#fundsGrid');
      if (grid && d.report) grid.innerHTML = `<div class="card card-2col"><div class="card-header"><h3><i class="fas fa-search"></i> Results</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(d.report)}</div></div></div>`;
    } catch (e) { alert(e.message); }
    btn.disabled = false; btn.innerHTML = '<i class="fas fa-search"></i> Search';
  });
}

function renderBanking() {
  const acctDiv = $('#bankingAccounts'); if (!acctDiv) return;
  const summaryDiv = $('#bankingSummary');
  API.getAccounts().then(d => {
    if (d?.data) {
      acctDiv.innerHTML = `<div class="card card-2col"><div class="card-header"><h3><i class="fas fa-wallet"></i> Accounts</h3></div><div class="card-body"><table class="table"><thead><tr><th>Account</th><th>Type</th><th>Balance</th><th>Currency</th><th>Status</th></tr></thead><tbody>${d.data.map(a => `<tr><td>${a.nickname||a.account_id}</td><td>${(a.type||'').replace('_',' ').toUpperCase()}</td><td>${fmtUSD(a.balance||0)}</td><td>${a.currency||'USD'}</td><td><span class="badge ${a.status==='active'?'badge-green':'badge-gray'}">${a.status||'active'}</span></td></tr>`).join('')}</tbody></table></div></div>`;
    } else { acctDiv.innerHTML = '<div class="card"><div class="card-body"><p class="text-center">No accounts found</p></div></div>'; }
  });
  API.getAccountSummary().then(d => {
    if (d?.data) {
      const s = d.data;
      const summaryHtml = `<div class="portfolio-summary"><div class="summary-card"><div class="summary-label">Total Balance</div><div class="summary-value">${fmtUSD(s.total_balance||0)}</div></div><div class="summary-card"><div class="summary-label">Active Accounts</div><div class="summary-value">${s.active_accounts||0}</div></div><div class="summary-card"><div class="summary-label">Pending Transfers</div><div class="summary-value">${s.pending_transfers||0}</div></div><div class="summary-card"><div class="summary-label">Outstanding Loans</div><div class="summary-value">${fmtUSD(s.total_loans||0)}</div></div></div>`;
      const existing = $('#bankingSummary');
      if (existing) existing.innerHTML = summaryHtml;
      else acctDiv.insertAdjacentHTML('beforebegin', `<div id="bankingSummary">${summaryHtml}</div>`);
    }
  });
  $$('.tab-btn[data-btab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-btab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.btab;
    ['accounts','transfers','loans','deposits','cards','bills'].forEach(t => $(`#banking${t.charAt(0).toUpperCase()+t.slice(1)}`).style.display = t === tab ? 'grid' : 'none');
    if (tab === 'transfers') API.getTransfers().then(d => { if (d?.data) $(`#bankingTransfers`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Transfers</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
    if (tab === 'loans') API.getLoans().then(d => { if (d?.data) $(`#bankingLoans`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Loans</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
    if (tab === 'deposits') API.getDeposits().then(d => { if (d?.data) $(`#bankingDeposits`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Deposits</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
    if (tab === 'cards') API.getCreditCards().then(d => { if (d?.data) $(`#bankingCards`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Credit Cards</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
    if (tab === 'bills') API.getBills().then(d => { if (d?.data) $(`#bankingBills`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Bills</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
  }));
}

function renderPayments() {
  const list = $('#paymentsList');
  if (!list) return;
  API.getPayments().then(d => {
    if (d?.data) {
      list.innerHTML = `<div class="card-header"><h3><i class="fas fa-list"></i> All Payments</h3></div><div class="card-body"><table class="table"><thead><tr><th>ID</th><th>Amount</th><th>Currency</th><th>Status</th><th>Rail</th></tr></thead><tbody>${d.data.slice(0,20).map(p => `<tr><td>${p.id?.slice(0,8)||'N/A'}</td><td>${fmtUSD(p.amount||0)}</td><td>${p.currency||'USD'}</td><td><span class="badge ${p.status==='completed'?'badge-green':'badge-yellow'}">${p.status||'pending'}</span></td><td>${p.rail||'N/A'}</td></tr>`).join('')}</tbody></table></div>`;
    } else { list.innerHTML = '<div class="card-body"><p class="text-center">No payments found</p></div>'; }
  });
  $$('.tab-btn[data-ptab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-ptab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.ptab;
    if (tab === 'swift') API.getSwiftBanks().then(d => { if (d) list.innerHTML = `<div class="card-header"><h3>SWIFT Participating Banks</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'sepa') API.getSepaMandates().then(d => { if (d) list.innerHTML = `<div class="card-header"><h3>SEPA Mandates</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'ach') API.getAchRoutes().then(d => { if (d) list.innerHTML = `<div class="card-header"><h3>ACH Routes</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'faster') API.getFasterPayments().then(d => { if (d) list.innerHTML = `<div class="card-header"><h3>Faster Payments Limits</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'all') renderPayments();
  }));
}

function renderWallets() {
  const bDiv = $('#walletsBanking'); if (!bDiv) return;
  API.getBankingWallets().then(d => {
    if (d?.wallets) bDiv.innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Banking Wallets</h3></div><div class="card-body"><pre>${JSON.stringify(d.wallets, null, 2)}</pre></div></div>`;
    else bDiv.innerHTML = '<div class="card"><div class="card-body"><p class="text-center">No banking wallets</p></div></div>';
  });
  $$('.tab-btn[data-wtab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-wtab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.wtab;
    ['banking','crypto','insurance'].forEach(t => $(`#wallets${t.charAt(0).toUpperCase()+t.slice(1)}`).style.display = t === tab ? 'grid' : 'none');
    if (tab === 'crypto') API.getCryptoWallets().then(d => { if (d?.wallets) $(`#walletsCrypto`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Crypto Wallets</h3></div><div class="card-body"><pre>${JSON.stringify(d.wallets, null, 2)}</pre></div></div>`; });
    if (tab === 'insurance') API.getInsuranceWallets().then(d => { if (d?.wallets) $(`#walletsInsurance`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Insurance Wallets</h3></div><div class="card-body"><pre>${JSON.stringify(d.wallets, null, 2)}</pre></div></div>`; });
  }));
}

function renderInsurance() {
  const polDiv = $('#insurancePolicies'); if (!polDiv) return;
  API.getInsurancePolicies().then(d => {
    if (d?.data) polDiv.innerHTML = `<div class="card card-2col"><div class="card-header"><h3><i class="fas fa-file-contract"></i> Policies</h3></div><div class="card-body"><table class="table"><thead><tr><th>Policy</th><th>Type</th><th>Coverage</th><th>Premium</th><th>Status</th></tr></thead><tbody>${d.data.map(p => `<tr><td>${p.coverage_name||p.policy_id?.slice(0,8)}</td><td>${(p.coverage_type||'').replace('_',' ').toUpperCase()}</td><td>$${fmt(p.coverage_amount||0)}</td><td>$${fmt(p.premium||0)}/mo</td><td><span class="badge badge-green">${p.status||'active'}</span></td></tr>`).join('')}</tbody></table></div></div>`;
    else polDiv.innerHTML = '<div class="card"><div class="card-body"><p class="text-center">No policies found</p></div></div>';
  });
  $$('.tab-btn[data-itab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-itab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.itab;
    ['policies','claims','premiums'].forEach(t => $(`#insurance${t.charAt(0).toUpperCase()+t.slice(1)}`).style.display = t === tab ? 'grid' : 'none');
    if (tab === 'claims') API.getInsuranceClaims().then(d => { if (d?.data) $(`#insuranceClaims`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Claims</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
    if (tab === 'premiums') API.getInsurancePremiums().then(d => { if (d?.data) $(`#insurancePremiums`).innerHTML = `<div class="card card-2col"><div class="card-header"><h3>Premiums</h3></div><div class="card-body"><pre>${JSON.stringify(d.data, null, 2)}</pre></div></div>`; });
  }));
}

function renderCompliance() {
  const amlDiv = $('#complianceAml'); if (!amlDiv) return;
  API.getComplianceScore('demo').then(d => {
    if (d) amlDiv.innerHTML = `<div class="card-header"><h3>Compliance Overview</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`;
    else amlDiv.innerHTML = '<div class="card-body"><p class="text-center">No compliance data</p></div>';
  });
  $$('.tab-btn[data-ctab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-ctab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.ctab;
    ['aml','kyc','sanctions','countries','reporting'].forEach(t => $(`#compliance${t.charAt(0).toUpperCase()+t.slice(1)}`).style.display = t === tab ? 'block' : 'none');
    if (tab === 'countries') API.getComplianceCountries().then(d => { if (d) $(`#complianceCountries`).innerHTML = `<div class="card-header"><h3>Country Rules</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
  }));
}

function renderSecurity() {
  const ovDiv = $('#securityOverview'); if (!ovDiv) return;
  API.getWafStats().then(d => {
    if (d) ovDiv.innerHTML = `<div class="card"><div class="card-header"><h3>WAF Stats</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div></div>`;
    else ovDiv.innerHTML = '<div class="card"><div class="card-body"><p class="text-center">Loading...</p></div></div>';
  });
  $$('.tab-btn[data-stab]').forEach(b => b.addEventListener('click', () => {
    $$('.tab-btn[data-stab]').forEach(x => x.classList.remove('active')); b.classList.add('active');
    const tab = b.dataset.stab;
    ['overview','waf','ids','siem','ddos','scan'].forEach(t => {
      const el = $(`#security${t.charAt(0).toUpperCase()+t.slice(1)}`);
      if (el) el.style.display = t === tab ? 'grid' : 'none';
    });
    if (tab === 'waf') API.getWafStats().then(d => { if (d) $(`#securityWaf`).innerHTML = `<div class="card-header"><h3>WAF Statistics</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'ids') API.getIdsEvents().then(d => { if (d) $(`#securityIds`).innerHTML = `<div class="card-header"><h3>IDS Events</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'siem') API.getSiemLogs().then(d => { if (d) $(`#securitySiem`).innerHTML = `<div class="card-header"><h3>SIEM Logs</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
    if (tab === 'ddos') API.getDdosStats().then(d => { if (d) $(`#securityDdos`).innerHTML = `<div class="card-header"><h3>DDoS Protection Stats</h3></div><div class="card-body"><pre>${JSON.stringify(d, null, 2)}</pre></div>`; });
  }));
}

function renderAIInsightFromCache(section, insight, updatedAt) {
  const containerId = `ai-${section}`;
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement('div');
    container.id = containerId;
    const page = document.getElementById(`page-${section}`);
    if (page) {
      const header = page.querySelector('.page-header');
      if (header) header.after(container);
      else page.prepend(container);
    }
  }
  const insightText = insight.length > 300 ? insight.substring(0, 300) + '...' : insight;
  container.innerHTML = `<div class="card insight-card" style="margin-bottom:16px"><div class="card-header"><h3><i class="fas fa-robot"></i> AI ${section.charAt(0).toUpperCase() + section.slice(1)} Insights</h3><span class="badge" style="font-size:10px">Confidence: 80%</span></div><div class="card-body"><p style="font-size:13px;color:var(--text-secondary);line-height:1.6">${mdToHtmlSimple(insightText)}</p><small style="color:var(--text-muted)">Updated: ${updatedAt || 'just now'}</small></div></div>`;
}

function showAIInsight(section, containerId) {
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement('div');
    container.id = containerId;
    const page = document.getElementById(`page-${section}`);
    if (page) {
      const header = page.querySelector('.page-header');
      if (header) header.after(container);
      else page.prepend(container);
    }
  }
  API.getInsights(section).then(d => {
    if (d?.insight) {
      const insightText = d.insight.length > 300 ? d.insight.substring(0, 300) + '...' : d.insight;
      container.innerHTML = `<div class="card insight-card" style="margin-bottom:16px"><div class="card-header"><h3><i class="fas fa-robot"></i> AI ${section.charAt(0).toUpperCase() + section.slice(1)} Insights</h3><span class="badge" style="font-size:10px">Confidence: ${Math.round((d.confidence || 0) * 100)}%</span></div><div class="card-body"><p style="font-size:13px;color:var(--text-secondary);line-height:1.6">${mdToHtmlSimple(insightText)}</p><small style="color:var(--text-muted)">Updated: ${d.updatedAt || 'just now'}</small></div></div>`;
    }
  });
}

function mdToHtmlSimple(md) {
  if (!md) return '';
  return md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
}

let _aiRefreshInterval = null;
const AI_REFRESH_MS = 120000;

function startAIRefresh(page) {
  if (_aiRefreshInterval) clearInterval(_aiRefreshInterval);
  const sectionMap = {
    dashboard: 'dashboard', stocks: 'stocks', indices: 'indices',
    forex: 'forex', crypto: 'crypto', commodities: 'commodities',
    bonds: 'bonds', options: 'options', funds: 'funds',
  };
  const section = sectionMap[page];
  if (!section) return;
  _aiRefreshInterval = setInterval(() => {
    const key = `_ai_insight_${section}`;
    if (CACHE[key]) {
      renderAIInsightFromCache(section, CACHE[key].insight, CACHE[key].updatedAt);
    } else {
      showAIInsight(section, `ai-${section}`);
    }
  }, AI_REFRESH_MS);
}

document.addEventListener('DOMContentLoaded', () => {
  initAuth();
  initNav();
  initMobile();
  updateClock();
  setInterval(updateClock, 1000);
  initResearch();
  initPortfolio();
  initWatchlist();
  initFundSearch();
  initCompare();
  initRisk();
  initAlerts();
  initSettings();
  initStockSearch();
});
