'use strict';

// ============================================================
// STATE
// ============================================================
const STATE = {
  portfolio: JSON.parse(localStorage.getItem('ira_portfolio') || '[]'),
  watchlist: JSON.parse(localStorage.getItem('ira_watchlist') || '[]'),
  alerts: JSON.parse(localStorage.getItem('ira_alerts') || '[]'),
  charts: {},
  currentPage: 'dashboard',
  settings: JSON.parse(localStorage.getItem('ira_settings') || '{}'),
};

// ============================================================
// UTILITY
// ============================================================
const $ = (s, p) => (p || document).querySelector(s);
const $$ = (s, p) => [...((p || document).querySelectorAll(s))];
const fmt = (n, d = 2) => { const v = Number(n); return isNaN(v) ? '0.00' : v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); };
const fmtUSD = (n) => '$' + fmt(n);
const fmtPct = (n) => (n >= 0 ? '+' : '') + fmt(n, 2) + '%';
const cls = (n) => n >= 0 ? 'up' : 'down';
const rand = (min, max) => Math.round((Math.random() * (max - min) + min) * 100) / 100;
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const genPrice = (base) => base * (1 + rand(-3, 3) / 100);

// ============================================================
// DATA
// ============================================================
const DATA = {
  indices: [
    { name: 'S&P 500', symbol: 'SPX', price: 5182.34, change: 0.62, high: 5195.20, low: 5158.10, volume: '2.1B', market: 'US', region: 'Americas', flag: '🇺🇸' },
    { name: 'NASDAQ', symbol: 'IXIC', price: 16302.14, change: 0.88, high: 16350.80, low: 16210.45, volume: '4.8B', market: 'US', region: 'Americas', flag: '🇺🇸' },
    { name: 'Dow Jones', symbol: 'DJI', price: 38904.70, change: 0.35, high: 38980.20, low: 38810.55, volume: '1.2B', market: 'US', region: 'Americas', flag: '🇺🇸' },
    { name: 'NIFTY 50', symbol: 'NIFTY', price: 22418.55, change: -0.23, high: 22480.30, low: 22390.15, volume: '1.5B', market: 'IN', region: 'APAC', flag: '🇮🇳' },
    { name: 'BSE SENSEX', symbol: 'SENSEX', price: 73892.15, change: 0.31, high: 74020.50, low: 73710.80, volume: '980M', market: 'IN', region: 'APAC', flag: '🇮🇳' },
    { name: 'NIFTY BANK', symbol: 'BANKNIFTY', price: 48215.30, change: -0.12, high: 48350.10, low: 48120.40, volume: '420M', market: 'IN', region: 'APAC', flag: '🇮🇳' },
    { name: 'STI Index', symbol: 'STI', price: 3215.40, change: -0.15, high: 3225.60, low: 3208.30, volume: '890M', market: 'SG', region: 'APAC', flag: '🇸🇬' },
    { name: 'NIKKEI 225', symbol: 'N225', price: 38215.60, change: 1.05, high: 38350.20, low: 38020.10, volume: '2.3B', market: 'JP', region: 'APAC', flag: '🇯🇵' },
    { name: 'FTSE 100', symbol: 'FTSE', price: 8214.80, change: 0.42, high: 8230.40, low: 8195.60, volume: '1.1B', market: 'GB', region: 'EMEA', flag: '🇬🇧' },
    { name: 'DAX 40', symbol: 'DAX', price: 18215.30, change: 0.55, high: 18280.70, low: 18160.20, volume: '980M', market: 'DE', region: 'EMEA', flag: '🇩🇪' },
    { name: 'Shanghai Composite', symbol: 'SHCOMP', price: 3125.80, change: -0.08, high: 3135.40, low: 3118.60, volume: '3.2B', market: 'CN', region: 'APAC', flag: '🇨🇳' },
    { name: 'Hang Seng', symbol: 'HSI', price: 17215.40, change: 0.78, high: 17290.30, low: 17140.20, volume: '1.8B', market: 'HK', region: 'APAC', flag: '🇭🇰' },
  ],
  movers: {
    gainers: [
      { name: 'NVDA', price: 892.45, change: 4.82 }, { name: 'AMD', price: 178.20, change: 3.65 },
      { name: 'AMZN', price: 188.90, change: 2.94 }, { name: 'RELIANCE', price: 2956.75, change: 2.45 },
      { name: 'META', price: 518.30, change: 2.18 }, { name: 'TCS', price: 3892.10, change: 1.95 },
    ],
    losers: [
      { name: 'TSLA', price: 178.50, change: -3.42 }, { name: 'INTC', price: 42.18, change: -2.85 },
      { name: 'BA', price: 182.30, change: -2.14 }, { name: 'WIPRO', price: 485.60, change: -1.78 },
      { name: 'BABA', price: 82.45, change: -1.52 }, { name: 'DBS', price: 35.60, change: -1.20 },
    ],
    volume: [
      { name: 'NVDA', price: 892.45, change: 4.82 }, { name: 'TSLA', price: 178.50, change: -3.42 },
      { name: 'AAPL', price: 183.92, change: 0.85 }, { name: 'SPY', price: 518.20, change: 0.42 },
      { name: 'QQQ', price: 442.15, change: 0.95 }, { name: 'RELIANCE', price: 2956.75, change: 2.45 },
    ],
  },
  news: [
    { title: 'Fed holds rates steady, signals 2 cuts later this year', source: 'Reuters', time: '2h ago', category: 'Macro' },
    { title: 'NVIDIA surpasses $3T market cap on AI chip demand', source: 'Bloomberg', time: '3h ago', category: 'Tech' },
    { title: 'Indian markets rally on strong Q4 earnings season', source: 'Economic Times', time: '1h ago', category: 'India' },
    { title: 'Singapore economy grows 2.8% in Q1, beats estimates', source: 'CNA', time: '4h ago', category: 'Singapore' },
    { title: 'Apple announces WWDC 2026 with AI-focused products', source: 'CNBC', time: '5h ago', category: 'Tech' },
    { title: 'Oil prices decline as OPEC+ considers output increase', source: 'WSJ', time: '2h ago', category: 'Commodities' },
    { title: 'SEBI proposes new framework for AI in Indian markets', source: 'Mint', time: '6h ago', category: 'India' },
    { title: 'DBS reports record profit for Q1 2026', source: 'Business Times', time: '3h ago', category: 'Singapore' },
  ],
  econCalendar: [
    { event: 'US CPI (May)', forecast: '3.2%', previous: '3.4%', importance: 'high' },
    { event: 'Fed Interest Rate Decision', forecast: '5.25%', previous: '5.50%', importance: 'high' },
    { event: 'US GDP QoQ (Q2)', forecast: '2.3%', previous: '1.6%', importance: 'high' },
    { event: 'India CPI (May)', forecast: '4.6%', previous: '4.8%', importance: 'medium' },
    { event: 'Singapore GDP QoQ (Q2)', forecast: '2.8%', previous: '2.2%', importance: 'medium' },
    { event: 'US Nonfarm Payrolls (Jun)', forecast: '220K', previous: '175K', importance: 'high' },
    { event: 'Japan Industrial Production', forecast: '1.5%', previous: '-0.6%', importance: 'medium' },
  ],
  forex: [
    { pair: 'EUR/USD', rate: 1.0824, change: 0.15, type: 'major' },
    { pair: 'GBP/USD', rate: 1.2685, change: -0.08, type: 'major' },
    { pair: 'USD/JPY', rate: 154.82, change: 0.32, type: 'major' },
    { pair: 'USD/CHF', rate: 0.9045, change: -0.12, type: 'major' },
    { pair: 'AUD/USD', rate: 0.6628, change: 0.22, type: 'major' },
    { pair: 'USD/CAD', rate: 1.3685, change: 0.05, type: 'major' },
    { pair: 'USD/INR', rate: 83.42, change: 0.08, type: 'exotic' },
    { pair: 'USD/SGD', rate: 1.3482, change: -0.04, type: 'exotic' },
    { pair: 'EUR/INR', rate: 90.35, change: 0.18, type: 'exotic' },
    { pair: 'EUR/GBP', rate: 0.8532, change: -0.06, type: 'minor' },
    { pair: 'GBP/JPY', rate: 196.45, change: 0.25, type: 'minor' },
    { pair: 'EUR/JPY', rate: 167.82, change: 0.12, type: 'minor' },
  ],
  crypto: [
    { name: 'Bitcoin', symbol: 'BTC', price: 68245, change: 2.34, icon: 'fab fa-bitcoin', color: '#f7931a' },
    { name: 'Ethereum', symbol: 'ETH', price: 3482, change: 1.85, icon: 'fab fa-ethereum', color: '#627eea' },
    { name: 'Solana', symbol: 'SOL', price: 148.25, change: 4.52, icon: 'fas fa-circle', color: '#00ffa3' },
    { name: 'XRP', symbol: 'XRP', price: 0.6245, change: -0.85, icon: 'fas fa-circle', color: '#23292f' },
    { name: 'Cardano', symbol: 'ADA', price: 0.4852, change: 2.15, icon: 'fas fa-circle', color: '#0033ad' },
    { name: 'Dogecoin', symbol: 'DOGE', price: 0.1582, change: -1.25, icon: 'fas fa-dog', color: '#c2a633' },
    { name: 'Polkadot', symbol: 'DOT', price: 7.24, change: 3.82, icon: 'fas fa-circle', color: '#e6007a' },
    { name: 'Avalanche', symbol: 'AVAX', price: 38.45, change: 5.12, icon: 'fas fa-circle', color: '#e84142' },
  ],
  commodities: [
    { name: 'Crude Oil (WTI)', symbol: 'CL', price: 78.45, change: -0.85, unit: 'bbl' },
    { name: 'Brent Oil', symbol: 'CO', price: 82.90, change: -0.62, unit: 'bbl' },
    { name: 'Gold', symbol: 'XAU', price: 2350.20, change: 0.45, unit: 'oz' },
    { name: 'Silver', symbol: 'XAG', price: 28.45, change: 0.85, unit: 'oz' },
    { name: 'Copper', symbol: 'HG', price: 4.52, change: 1.25, unit: 'lb' },
    { name: 'Natural Gas', symbol: 'NG', price: 2.85, change: -1.45, unit: 'MMBtu' },
    { name: 'Corn', symbol: 'C', price: 4.82, change: 0.35, unit: 'bu' },
    { name: 'Wheat', symbol: 'W', price: 6.45, change: -0.55, unit: 'bu' },
  ],
  bonds: [
    { name: 'US 10Y Treasury', symbol: 'US10Y', yield: 4.42, change: -0.03, type: 'government' },
    { name: 'US 2Y Treasury', symbol: 'US2Y', yield: 4.82, change: 0.02, type: 'government' },
    { name: 'US 30Y Treasury', symbol: 'US30Y', yield: 4.65, change: -0.05, type: 'government' },
    { name: 'India 10Y Bond', symbol: 'IN10Y', yield: 7.02, change: -0.02, type: 'government' },
    { name: 'Singapore 10Y Bond', symbol: 'SG10Y', yield: 3.25, change: 0.01, type: 'government' },
    { name: 'UK 10Y Gilt', symbol: 'UK10Y', yield: 4.18, change: -0.04, type: 'government' },
    { name: 'IG Corporate Bond ETF', symbol: 'LQD', yield: 5.12, change: -0.01, type: 'corporate' },
    { name: 'High Yield Bond ETF', symbol: 'HYG', yield: 7.85, change: 0.03, type: 'corporate' },
  ],
  ipos: [
    { name: 'Stripe Inc.', symbol: 'STRIPE', exchange: 'NYSE', price: 'N/A', date: 'Jun 2026', type: 'Tech', status: 'upcoming' },
    { name: 'Reddit', symbol: 'RDDT', exchange: 'NYSE', price: 58.45, date: 'Mar 2024', type: 'Tech', status: 'listed', change: 18.5 },
    { name: 'Arm Holdings', symbol: 'ARM', exchange: 'NASDAQ', price: 124.80, date: 'Sep 2023', type: 'Semicon', status: 'listed', change: 112.4 },
    { name: 'OYO Hotels', symbol: 'OYO', exchange: 'NSE', price: 'N/A', date: '2026', type: 'Hospitality', status: 'upcoming' },
    { name: 'Swiggy', symbol: 'SWIGGY', exchange: 'NSE', price: 'N/A', date: '2025', type: 'Food Tech', status: 'upcoming' },
    { name: 'ByteDance (Singapore)', symbol: 'BYTED', exchange: 'SGX', price: 'N/A', date: 'TBD', type: 'Tech', status: 'upcoming' },
    { name: 'Kraken', symbol: 'KRAKEN', exchange: 'NASDAQ', price: 'N/A', date: '2026', type: 'Crypto', status: 'upcoming' },
    { name: 'Chubb Ltd', symbol: 'CHUBB', exchange: 'SGX', price: 28.50, date: '2025', type: 'Insurance', status: 'listed', change: 5.2 },
  ],
  trending: [
    { name: 'NVDA', price: 892.45, change: 4.82, sector: 'Technology' },
    { name: 'AAPL', price: 183.92, change: 0.85, sector: 'Technology' },
    { name: 'TSLA', price: 178.50, change: -3.42, sector: 'Automotive' },
    { name: 'RELIANCE', price: 2956.75, change: 2.45, sector: 'Conglomerate' },
    { name: 'DBS', price: 35.60, change: -1.20, sector: 'Banking' },
    { name: 'TCS', price: 3892.10, change: 1.95, sector: 'IT Services' },
  ],
};

// ============================================================
// INIT NAV
// ============================================================
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

// ============================================================
// CLOCK + TICKER
// ============================================================
function updateClock() {
  $('#clock').textContent = new Date().toLocaleString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short' });
}
function initTicker() {
  const t = $('#marketTicker');
  if (t) {
    t.innerHTML = DATA.indices.slice(0, 8).map(i => `<div class="ticker-item ${cls(i.change)}"><span class="ticker-sym">${i.symbol}</span><span class="ticker-val">${fmt(i.price)}</span><span class="ticker-chg">${fmtPct(i.change)}</span></div>`).join('');
  }
  setInterval(() => {
    $$('.ticker-item').forEach(el => {
      const sym = el.querySelector('.ticker-sym')?.textContent;
      const idx = DATA.indices.find(i => i.symbol === sym);
      if (!idx) return;
      const chg = rand(-0.5, 0.5); idx.change = +(idx.change + chg / 10).toFixed(2); idx.price = +(idx.price * (1 + chg / 5000)).toFixed(2);
      el.querySelector('.ticker-val').textContent = fmt(idx.price, idx.price < 100 ? 4 : 2);
      el.querySelector('.ticker-chg').textContent = fmtPct(idx.change);
      el.className = 'ticker-item ' + cls(idx.change);
    });
  }, 3000);
}

// ============================================================
// REFRESH
// ============================================================
$('#refreshBtn')?.addEventListener('click', () => {
  $('#refreshBtn i').classList.add('fa-spin');
  setTimeout(() => { renderPage(STATE.currentPage); setTimeout(() => $('#refreshBtn i').classList.remove('fa-spin'), 500); }, 300);
});

// ============================================================
// RENDER DISPATCH
// ============================================================
function renderPage(page) {
  switch (page) {
    case 'dashboard': renderDashboard(); break;
    case 'stocks': renderStocks(); break;
    case 'indices': renderAllIndices(); break;
    case 'forex': renderForex(); break;
    case 'crypto': renderCrypto(); break;
    case 'commodities': renderCommodities(); break;
    case 'bonds': renderBonds(); break;
    case 'options': break;
    case 'ipos': renderIPOs(); break;
    case 'watchlist': renderWatchlist(); break;
    case 'portfolio': renderPortfolio(); break;
    case 'screener': renderScreener(); break;
    case 'alerts': renderAlerts(); break;
    case 'settings': break;
  }
}

// ============================================================
// DASHBOARD
// ============================================================
function renderDashboard() {
  renderIndices($('#dashMarketFilter')?.value || 'all');
  renderMovers('gainers');
  $('#newsList').innerHTML = DATA.news.map(n => `<div class="news-item"><div class="news-title">${n.title}</div><div class="news-meta"><span class="news-source">${n.source}</span><span>${n.time}</span><span>${n.category}</span></div></div>`).join('');
  $('#econCalendar').innerHTML = DATA.econCalendar.map(e => `<div class="econ-item"><div><span class="econ-event">${e.event}</span>${e.importance === 'high' ? '<span class="econ-important">HIGH</span>' : ''}</div><div class="econ-forecast">F: ${e.forecast} | P: ${e.previous}</div></div>`).join('');
  renderMarketChart();
}
function renderIndices(filter) {
  const grid = $('#indicesGrid');
  if (!grid) return;
  const items = filter && filter !== 'all' ? DATA.indices.filter(i => i.market === filter) : DATA.indices;
  grid.innerHTML = items.map(i => `<div class="indice-card" data-market="${i.market}"><div class="indice-header"><span class="indice-name">${i.flag} ${i.name}</span><span class="indice-flag">${i.symbol}</span></div><div class="indice-price">${fmtUSD(i.price)}</div><div class="indice-change ${cls(i.change)}"><i class="fas fa-${i.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(i.change)}</div><div class="indice-detail"><span>H: ${fmtUSD(i.high)}</span><span>L: ${fmtUSD(i.low)}</span><span>Vol: ${i.volume}</span></div></div>`).join('');
}
$('#dashMarketFilter')?.addEventListener('change', (e) => renderIndices(e.target.value));

function renderMovers(type) {
  const c = $('#moversList'); if (!c) return;
  const items = DATA.movers[type] || [];
  c.innerHTML = items.map(m => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${m.name}</span><span class="mover-price">${fmtUSD(m.price)}</span></div><span class="mover-change ${cls(m.change)}">${fmtPct(m.change)}</span></div>`).join('');
}
$$('.tab-btn[data-mover]').forEach(b => b.addEventListener('click', () => { $$('.tab-btn[data-mover]').forEach(x => x.classList.remove('active')); b.classList.add('active'); renderMovers(b.dataset.mover); }));

function renderMarketChart() {
  const canvas = $('#marketChart'); if (!canvas) return;
  if (STATE.charts.market) STATE.charts.market.destroy();
  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  STATE.charts.market = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'S&P 500', data: labels.map(() => rand(5000, 5300)), borderColor: '#3b82f6', tension: 0.3, fill: false },
      { label: 'NASDAQ', data: labels.map(() => rand(16000, 16800)), borderColor: '#22c55e', tension: 0.3, fill: false },
      { label: 'NIFTY 50', data: labels.map(() => rand(22000, 22800)), borderColor: '#eab308', tension: 0.3, fill: false },
    ]},
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0', font: { size: 11 } } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 10 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 10 } } } } },
  });
}

// ============================================================
// STOCKS
// ============================================================
function renderStocks() {
  const cont = $('#trendingStocks');
  if (cont) cont.innerHTML = DATA.trending.map(s => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${s.name}</span><span class="mover-price">${s.sector} · ${fmtUSD(s.price)}</span></div><span class="mover-change ${cls(s.change)}">${fmtPct(s.change)}</span></div>`).join('');
  renderSectorChart();
}
function renderSectorChart() {
  const canvas = $('#sectorChart'); if (!canvas) return;
  if (STATE.charts.sector) STATE.charts.sector.destroy();
  const sectors = ['Technology', 'Banking', 'Automotive', 'Energy', 'Healthcare', 'Consumer', 'IT Services'];
  STATE.charts.sector = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels: sectors, datasets: [{ label: 'Sector Performance (%)', data: sectors.map(() => rand(-3, 6)), backgroundColor: sectors.map(() => '#3b82f680'), borderColor: '#3b82f6', borderWidth: 1 }] },
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

// ============================================================
// ALL INDICES
// ============================================================
function renderAllIndices(filter) {
  const grid = $('#allIndicesGrid'); if (!grid) return;
  const items = filter && filter !== 'all' ? DATA.indices.filter(i => i.region === filter) : DATA.indices;
  grid.innerHTML = items.map(i => `<div class="indice-card"><div class="indice-header"><span class="indice-name">${i.flag} ${i.name}</span><span class="indice-flag">${i.symbol}</span></div><div class="indice-price">${fmtUSD(i.price)}</div><div class="indice-change ${cls(i.change)}"><i class="fas fa-${i.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(i.change)}</div><div class="indice-detail"><span>H: ${fmtUSD(i.high)}</span><span>L: ${fmtUSD(i.low)}</span></div></div>`).join('');
  renderIndicesComparisonChart();
}
$('#indicesFilter')?.addEventListener('change', (e) => renderAllIndices(e.target.value));

function renderIndicesComparisonChart() {
  const canvas = $('#indicesChart'); if (!canvas) return;
  if (STATE.charts.indices) STATE.charts.indices.destroy();
  STATE.charts.indices = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels: DATA.indices.map(i => i.symbol), datasets: [{ label: 'YTD Change (%)', data: DATA.indices.map(() => rand(-5, 15)), backgroundColor: DATA.indices.map(i => i.change >= 0 ? '#22c55e80' : '#ef444480'), borderColor: DATA.indices.map(i => i.change >= 0 ? '#22c55e' : '#ef4444'), borderWidth: 1 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 9 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

// ============================================================
// FOREX
// ============================================================
function renderForex(filter) {
  const grid = $('#forexGrid'); if (!grid) return;
  const items = filter && filter !== 'all' ? DATA.forex.filter(f => f.type === filter) : DATA.forex;
  grid.innerHTML = items.map(f => `<div class="forex-card"><div class="fx-pair">${f.pair}</div><div class="fx-rate">${fmt(f.rate, f.rate < 10 ? 4 : 2)}</div><div class="fx-change ${cls(f.change)}"><i class="fas fa-${f.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(f.change)}</div></div>`).join('');
  renderForexChart();
}
$('#forexFilter')?.addEventListener('change', (e) => renderForex(e.target.value));

function renderForexChart() {
  const canvas = $('#forexChart'); if (!canvas) return;
  if (STATE.charts.forex) STATE.charts.forex.destroy();
  const labels = Array.from({ length: 20 }, (_, i) => `Day ${i + 1}`);
  STATE.charts.forex = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [{ label: 'EUR/USD', data: labels.map(() => rand(1.07, 1.10)), borderColor: '#3b82f6', tension: 0.3, fill: false }] },
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0' } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

// ============================================================
// CRYPTO
// ============================================================
function renderCrypto() {
  const grid = $('#cryptoGrid'); if (!grid) return;
  grid.innerHTML = DATA.crypto.map(c => `<div class="crypto-card"><div class="crypto-icon" style="color:${c.color}"><i class="${c.icon}"></i></div><div class="crypto-name">${c.name} <span style="color:var(--text-muted);font-size:12px">${c.symbol}</span></div><div class="crypto-price">${fmtUSD(c.price)}</div><div class="crypto-change ${cls(c.change)}">${fmtPct(c.change)}</div></div>`).join('');
  renderCryptoChart();
}
function renderCryptoChart() {
  const canvas = $('#cryptoChart'); if (!canvas) return;
  if (STATE.charts.crypto) STATE.charts.crypto.destroy();
  const labels = Array.from({ length: 30 }, (_, i) => `D${i + 1}`);
  STATE.charts.crypto = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'BTC', data: labels.map(() => rand(65000, 72000)), borderColor: '#f7931a', tension: 0.3 },
      { label: 'ETH', data: labels.map(() => rand(3200, 3600)), borderColor: '#627eea', tension: 0.3 },
    ]},
    options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0', font: { size: 11 } } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a', font: { size: 9 } } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } },
  });
}

// ============================================================
// COMMODITIES
// ============================================================
function renderCommodities() {
  const grid = $('#commoditiesGrid'); if (!grid) return;
  grid.innerHTML = DATA.commodities.map(c => `<div class="commodity-card"><div class="crypto-name">${c.name} <span style="color:var(--text-muted);font-size:12px">${c.symbol}</span></div><div class="crypto-price">${fmtUSD(c.price)}</div><div class="crypto-change ${cls(c.change)}">${fmtPct(c.change)}</div></div>`).join('');
}

// ============================================================
// BONDS
// ============================================================
function renderBonds() {
  const grid = $('#bondsGrid'); if (!grid) return;
  grid.innerHTML = DATA.bonds.map(b => `<div class="bond-card"><div class="crypto-name">${b.name} <span style="color:var(--text-muted);font-size:12px">${b.symbol}</span></div><div class="crypto-price">${fmt(b.yield, 2)}%</div><div class="crypto-change ${cls(-b.change)}"><i class="fas fa-${b.change >= 0 ? 'caret-up' : 'caret-down'}"></i> ${fmtPct(b.change)}</div></div>`).join('');
}

// ============================================================
// IPOS
// ============================================================
function renderIPOs() {
  const grid = $('#iposGrid'); if (!grid) return;
  grid.innerHTML = DATA.ipos.map(ipo => `<div class="ipo-card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span class="crypto-name">${ipo.name}</span><span class="badge-lg" style="${ipo.status === 'listed' ? 'color:var(--up);background:rgba(34,197,94,0.1)' : 'color:var(--accent-yellow);background:rgba(234,179,8,0.1)'}">${ipo.status.toUpperCase()}</span></div><div style="font-size:12px;color:var(--text-muted)">${ipo.exchange} · ${ipo.type} · ${ipo.date}</div><div style="margin-top:6px;font-size:14px;font-weight:600">${ipo.status === 'listed' ? fmtUSD(ipo.price) + ' ' + (ipo.change ? `<span class="${cls(ipo.change)}">${fmtPct(ipo.change)}</span>` : '') : 'Pricing TBD'}</div></div>`).join('');
}

// ============================================================
// RESEARCH
// ============================================================
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
  return md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/^### (.+)$/gm, '<h4>$1</h4>').replace(/^## (.+)$/gm, '<h3>$1</h3>').replace(/^# (.+)$/gm, '<h2>$1</h2>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
}

// ============================================================
// PORTFOLIO
// ============================================================
function renderPortfolio() {
  const h = STATE.portfolio; const tv = h.reduce((s, x) => s + x.qty * (x.currentPrice || x.cost), 0);
  const tc = h.reduce((s, x) => s + x.qty * x.cost, 0); const tp = tv - tc;
  const ret = tc > 0 ? (tp / tc) * 100 : 0;
  $('#portfolioSummary').innerHTML = `
    <div class="summary-card"><span class="summary-label">Total Value</span><span class="summary-value">${fmtUSD(tv)}</span></div>
    <div class="summary-card"><span class="summary-label">Total P&L</span><span class="summary-value ${cls(tp)}">${tp >= 0 ? '+' : ''}${fmtUSD(tp)}</span></div>
    <div class="summary-card"><span class="summary-label">Day Change</span><span class="summary-value">${fmtUSD(tv * rand(-0.5, 0.5) / 100)}</span></div>
    <div class="summary-card"><span class="summary-label">Returns</span><span class="summary-value ${cls(ret)}">${fmtPct(ret)}</span></div>`;
  const body = $('#holdingsBody');
  if (h.length === 0) body.innerHTML = '<tr><td colspan="10" class="text-center">No holdings yet.</td></tr>';
  else body.innerHTML = h.map((x, i) => { const mv = x.qty * (x.currentPrice || x.cost); const pnl = (x.currentPrice || x.cost) - x.cost; const pp = x.cost > 0 ? (pnl / x.cost) * 100 : 0; return `<tr><td><strong>${x.ticker}</strong></td><td>${x.type}</td><td>${x.market || 'US'}</td><td>${x.qty}</td><td>${fmtUSD(x.cost)}</td><td>${fmtUSD(x.currentPrice || x.cost)}</td><td>${fmtUSD(mv)}</td><td class="${cls(pnl)}">${fmtUSD(pnl * x.qty)}</td><td class="${cls(pp)}">${fmtPct(pp)}</td><td><button class="btn btn-sm" onclick="removeHolding(${i})"><i class="fas fa-trash"></i></button></td></tr>`; }).join('');
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
  STATE.portfolio.push({ ticker: t.toUpperCase(), type: type || 'stock', qty: Number(qty) || 1, cost: Number(cost) || 0, market: market || 'US', currentPrice: Number(cost) * (1 + rand(-5, 5) / 100), addedAt: new Date().toISOString() });
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

// ============================================================
// WATCHLIST
// ============================================================
function renderWatchlist() {
  const body = $('#watchlistBody'); const w = STATE.watchlist;
  if (w.length === 0) body.innerHTML = '<p class="text-center">Your watchlist is empty. Add symbols to track.</p>';
  else body.innerHTML = w.map((x, i) => `<div class="mover-item"><div class="mover-info"><span class="mover-name">${x.ticker}</span><span class="mover-price">${x.market || 'US'} · Added ${new Date(x.addedAt).toLocaleDateString()}</span></div><button class="btn btn-sm" onclick="removeWatch(${i})"><i class="fas fa-times"></i></button></div>`).join('');
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

// ============================================================
// SCREENER
// ============================================================
function renderScreener() {
  const cont = $('#screenerResults'); if (!cont) return;
  const stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD'];
  const rows = stocks.map(s => { const p = rand(50, 900); const c = rand(-5, 8); return `<tr><td><strong>${s}</strong></td><td>${fmtUSD(p)}</td><td class="${cls(c)}">${fmtPct(c)}</td><td>${fmtUSD(p * rand(1, 50))}B</td><td>${fmt(rand(10, 80))}</td><td>${fmt(rand(0.5, 5), 2)}M</td></tr>`; }).join('');
  cont.innerHTML = `<div style="overflow-x:auto"><table class="screener-table"><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Mkt Cap</th><th>P/E</th><th>Volume</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
$('#screenerBtn')?.addEventListener('click', () => renderScreener());

// ============================================================
// OPTIONS & FUTURES
// ============================================================
$('#optionsSearchBtn')?.addEventListener('click', async () => {
  const t = $('#optionsTicker')?.value.trim().toUpperCase(); if (!t) return;
  const type = $('#optionsType')?.value || 'options';
  const cont = $('#optionsResults');
  cont.innerHTML = `<div class="card"><div class="card-header"><h3>${t} ${type.toUpperCase()} Chain</h3></div><div class="card-body"><div class="loader"></div></div></div>`;
  try {
    const data = await API.query({ query: `Show ${type} chain and analysis for ${t}`, session_id: 'opt_' + Date.now() });
    cont.innerHTML = `<div class="card"><div class="card-header"><h3>${t} ${type.toUpperCase()}</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(data.report || data.analysis || 'No data')}</div></div></div>`;
  } catch (e) { cont.innerHTML = `<div class="context-box error">${e.message}</div>`; }
});

// ============================================================
// COMPARE
// ============================================================
function initCompare() {
  $('#compareBtn')?.addEventListener('click', async () => {
    const t1 = $('#compTicker1').value.trim().toUpperCase(); const t2 = $('#compTicker2').value.trim().toUpperCase();
    const t3 = $('#compTicker3').value.trim().toUpperCase(); if (!t1 || !t2) return;
    const r = $('#comparisonResults'); r.style.display = 'block'; r.innerHTML = '<div class="loader" style="height:200px"></div>';
    try {
      const q = `Compare ${t1} vs ${t2}${t3 ? ' vs ' + t3 : ''} across financial metrics, valuation, growth, and risks`;
      const d = await API.query({ query: q, session_id: 'cmp_' + Date.now() });
      r.innerHTML = `<div class="card"><div class="card-header"><h3><i class="fas fa-balance-scale"></i> ${t1} vs ${t2}${t3 ? ' vs ' + t3 : ''}</h3></div><div class="card-body"><div class="markdown-body">${mdToHtml(d.report || d.analysis || 'No data')}</div></div></div>`;
      const tickers = [t1, t2]; if (t3) tickers.push(t3);
      r.innerHTML += `<div style="margin-top:16px"><canvas id="comparisonChart"></canvas></div>`;
      renderComparisonChart(tickers);
    } catch (e) { r.innerHTML = `<div class="context-box error">${e.message}</div>`; }
  });
}
function renderComparisonChart(tickers) {
  const canvas = $('#comparisonChart'); if (!canvas) return;
  if (STATE.charts.compare) STATE.charts.compare.destroy();
  const colors = ['#3b82f6', '#22c55e', '#eab308'];
  STATE.charts.compare = new Chart(canvas.getContext('2d'), { type: 'bar', data: { labels: ['Revenue', 'Net Income', 'EPS', 'P/E', 'Growth', 'Moat'], datasets: tickers.map((t, i) => ({ label: t, data: [rand(50, 500), rand(10, 100), rand(1, 10), rand(15, 40), rand(5, 30), rand(50, 95)], backgroundColor: colors[i] + '80', borderColor: colors[i], borderWidth: 1 })) }, options: { responsive: true, plugins: { legend: { labels: { color: '#9aa0b0', font: { size: 11 } } } }, scales: { x: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } }, y: { grid: { color: '#2a3142' }, ticks: { color: '#5f677a' } } } } });
}

// ============================================================
// RISK
// ============================================================
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

// ============================================================
// ALERTS
// ============================================================
function renderAlerts() {
  const c = $('#alertsList'); const a = STATE.alerts;
  if (a.length === 0) c.innerHTML = '<p class="text-center">No alerts set. Create alerts to get notified.</p>';
  else c.innerHTML = a.map((x, i) => `<div class="alert-item"><div class="alert-info"><span class="alert-ticker">${x.ticker}</span> ${x.condition === 'above' ? '>' : x.condition === 'below' ? '<' : '±'} ${x.value} <span class="alert-condition">(${x.condition})</span></div><button class="alert-remove" onclick="removeAlert(${i})"><i class="fas fa-trash"></i></button></div>`).join('');
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

// ============================================================
// SETTINGS
// ============================================================
function initSettings() {
  // Load saved provider
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
}

// ============================================================
// MODAL CLOSE FOR ALL
// ============================================================
$$('.modal .modal-close').forEach(b => b.addEventListener('click', () => { b.closest('.modal').classList.remove('show'); }));

// ============================================================
// FUND SEARCH
// ============================================================
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

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initNav(); initMobile(); initTicker(); updateClock(); setInterval(updateClock, 1000);
  initResearch(); initPortfolio(); initWatchlist(); initFundSearch(); initCompare(); initRisk(); initAlerts(); initSettings(); initStockSearch();
  renderDashboard(); renderStocks(); renderAllIndices(); renderForex(); renderCrypto(); renderCommodities(); renderBonds(); renderIPOs(); renderWatchlist(); renderAlerts(); renderScreener();

  // Dynamic updates
  setInterval(() => {
    if (STATE.currentPage === 'dashboard') { renderIndices($('#dashMarketFilter')?.value || 'all'); }
  }, 30000);
});
