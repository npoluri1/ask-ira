const API = {
  async query(payload) {
    const res = await fetch('/api/v1/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail?.[0]?.msg || 'API error'); }
    return res.json();
  },

  async health() {
    const res = await fetch('/health');
    return res.json();
  },

  async metrics() {
    const res = await fetch('/metrics');
    return res.json();
  },

  async fetchStockPrice(ticker) {
    return API.query({ query: `What is the current stock price of ${ticker}?`, session_id: '_price' });
  },

  async fetchFinancials(ticker) {
    return API.query({ query: `Get financials for ${ticker}`, session_id: '_fin' });
  },

  SIMULATED: {
    indices: [
      { name: 'S&P 500', symbol: 'SPX', price: 5182.34, change: 0.62, high: 5195.20, low: 5158.10, volume: '2.1B', market: 'US', flag: '🇺🇸' },
      { name: 'NASDAQ', symbol: 'IXIC', price: 16302.14, change: 0.88, high: 16350.80, low: 16210.45, volume: '4.8B', market: 'US', flag: '🇺🇸' },
      { name: 'Dow Jones', symbol: 'DJI', price: 38904.70, change: 0.35, high: 38980.20, low: 38810.55, volume: '1.2B', market: 'US', flag: '🇺🇸' },
      { name: 'NIFTY 50', symbol: 'NIFTY', price: 22418.55, change: -0.23, high: 22480.30, low: 22390.15, volume: '1.5B', market: 'IN', flag: '🇮🇳' },
      { name: 'BSE SENSEX', symbol: 'SENSEX', price: 73892.15, change: 0.31, high: 74020.50, low: 73710.80, volume: '980M', market: 'IN', flag: '🇮🇳' },
      { name: 'NIFTY BANK', symbol: 'BANKNIFTY', price: 48215.30, change: -0.12, high: 48350.10, low: 48120.40, volume: '420M', market: 'IN', flag: '🇮🇳' },
      { name: 'STI Index', symbol: 'STI', price: 3215.40, change: -0.15, high: 3225.60, low: 3208.30, volume: '890M', market: 'SG', flag: '🇸🇬' },
      { name: 'NIKKEI 225', symbol: 'N225', price: 38215.60, change: 1.05, high: 38350.20, low: 38020.10, volume: '2.3B', market: 'JP', flag: '🇯🇵' },
      { name: 'FTSE 100', symbol: 'FTSE', price: 8214.80, change: 0.42, high: 8230.40, low: 8195.60, volume: '1.1B', market: 'GB', flag: '🇬🇧' },
      { name: 'DAX 40', symbol: 'DAX', price: 18215.30, change: 0.55, high: 18280.70, low: 18160.20, volume: '980M', market: 'DE', flag: '🇩🇪' },
      { name: 'Shanghai Composite', symbol: 'SHCOMP', price: 3125.80, change: -0.08, high: 3135.40, low: 3118.60, volume: '3.2B', market: 'CN', flag: '🇨🇳' },
      { name: 'Hang Seng', symbol: 'HSI', price: 17215.40, change: 0.78, high: 17290.30, low: 17140.20, volume: '1.8B', market: 'HK', flag: '🇭🇰' },
    ],

    movers: {
      gainers: [
        { name: 'NVDA', price: 892.45, change: 4.82 },
        { name: 'AMD', price: 178.20, change: 3.65 },
        { name: 'AMZN', price: 188.90, change: 2.94 },
        { name: 'RELIANCE', price: 2956.75, change: 2.45 },
        { name: 'META', price: 518.30, change: 2.18 },
        { name: 'TCS', price: 3892.10, change: 1.95 },
      ],
      losers: [
        { name: 'TSLA', price: 178.50, change: -3.42 },
        { name: 'INTC', price: 42.18, change: -2.85 },
        { name: 'BA', price: 182.30, change: -2.14 },
        { name: 'WIPRO', price: 485.60, change: -1.78 },
        { name: 'BABA', price: 82.45, change: -1.52 },
        { name: 'DBS', price: 35.60, change: -1.20 },
      ],
    },

    news: [
      { title: 'Fed holds rates steady, signals 2 cuts later this year', source: 'Reuters', time: '2h ago', category: 'Macro' },
      { title: 'NVIDIA surpasses $3T market cap on AI chip demand', source: 'Bloomberg', time: '3h ago', category: 'Tech' },
      { title: 'Indian markets rally on strong Q4 earnings season', source: 'Economic Times', time: '1h ago', category: 'India' },
      { title: 'Singapore economy grows 2.8% in Q1, beats estimates', source: 'CNA', time: '4h ago', category: 'Singapore' },
      { title: 'Apple announces WWDC 2025 with AI-focused products', source: 'CNBC', time: '5h ago', category: 'Tech' },
      { title: 'Oil prices decline as OPEC+ considers output increase', source: 'WSJ', time: '2h ago', category: 'Commodities' },
      { title: 'SEBI proposes new framework for AI in Indian markets', source: 'Mint', time: '6h ago', category: 'India' },
      { title: 'DBS reports record profit for Q1 2025', source: 'Business Times', time: '3h ago', category: 'Singapore' },
    ],

    econCalendar: [
      { event: 'US CPI (Apr)', forecast: '3.3%', previous: '3.5%', importance: 'high' },
      { event: 'Fed Interest Rate Decision', forecast: '5.50%', previous: '5.50%', importance: 'high' },
      { event: 'US GDP QoQ (Q1)', forecast: '2.1%', previous: '3.2%', importance: 'high' },
      { event: 'India CPI (Apr)', forecast: '4.8%', previous: '4.9%', importance: 'medium' },
      { event: 'Singapore GDP QoQ (Q1)', forecast: '2.5%', previous: '2.2%', importance: 'medium' },
      { event: 'US Nonfarm Payrolls (May)', forecast: '240K', previous: '303K', importance: 'high' },
      { event: 'Japan Industrial Production', forecast: '1.2%', previous: '-0.6%', importance: 'medium' },
    ],

    etfs: [
      { name: 'SPDR S&P 500 ETF', symbol: 'SPY', category: 'Large Cap', ytd: 10.42, oneY: 22.15, expRatio: 0.09 },
      { name: 'Invesco QQQ Trust', symbol: 'QQQ', category: 'Tech', ytd: 12.85, oneY: 28.40, expRatio: 0.20 },
      { name: 'Vanguard Total Market', symbol: 'VTI', category: 'Total Market', ytd: 9.80, oneY: 20.55, expRatio: 0.03 },
      { name: 'iShares MSCI India', symbol: 'INDA', category: 'India', ytd: 6.25, oneY: 18.30, expRatio: 0.65 },
      { name: 'Nippon India ETF Nifty 50', symbol: 'NIFTYBEES', category: 'India', ytd: 7.80, oneY: 19.45, expRatio: 0.05 },
      { name: 'Nikko AM STI ETF', symbol: 'STIETF', category: 'Singapore', ytd: 4.20, oneY: 8.90, expRatio: 0.30 },
    ],

    mutualFunds: [
      { name: 'HDFC Mid-Cap Opportunities Fund', category: 'Mid-Cap', oneY: 32.5, threeY: 24.8, fiveY: 18.2 },
      { name: 'SBI Bluechip Fund', category: 'Large-Cap', oneY: 22.4, threeY: 18.6, fiveY: 15.2 },
      { name: 'Axis Growth Opportunities Fund', category: 'Flexi-Cap', oneY: 28.6, threeY: 21.2, fiveY: 16.8 },
      { name: 'ICICI Prudential Value Discovery', category: 'Value', oneY: 25.2, threeY: 20.4, fiveY: 14.6 },
      { name: 'Mirae Asset Emerging Bluechip', category: 'Large & Mid', oneY: 30.8, threeY: 22.6, fiveY: 17.4 },
      { name: 'Kotak Emerging Equity Fund', category: 'Mid-Cap', oneY: 26.4, threeY: 19.8, fiveY: 15.8 },
    ],

    globalMarkets() {
      const regions = {
        'US': { name: 'United States', flag: '🇺🇸', indices: ['S&P 500', 'NASDAQ', 'Dow Jones'] },
        'IN': { name: 'India', flag: '🇮🇳', indices: ['NIFTY 50', 'BSE SENSEX', 'NIFTY BANK'] },
        'SG': { name: 'Singapore', flag: '🇸🇬', indices: ['STI Index'] },
        'JP': { name: 'Japan', flag: '🇯🇵', indices: ['NIKKEI 225'] },
        'GB': { name: 'United Kingdom', flag: '🇬🇧', indices: ['FTSE 100'] },
        'DE': { name: 'Germany', flag: '🇩🇪', indices: ['DAX 40'] },
        'CN': { name: 'China', flag: '🇨🇳', indices: ['Shanghai Composite'] },
        'HK': { name: 'Hong Kong', flag: '🇭🇰', indices: ['Hang Seng'] },
      };
      return Object.entries(regions).map(([code, r]) => ({
        ...r,
        code,
        indices: r.indices.map(name => this.indices.find(i => i.name === name)).filter(Boolean),
      }));
    },
  },
};
