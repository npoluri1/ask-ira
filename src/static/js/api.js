const TOKEN_KEY = 'ira_access_token';
const REFRESH_KEY = 'ira_refresh_token';
const USER_KEY = 'ira_user';

const API = {
  _cache: {},
  _pending: {},

  // --- Token management ---
  getToken() { return localStorage.getItem(TOKEN_KEY); },
  getRefreshToken() { return localStorage.getItem(REFRESH_KEY); },
  getUser() { const u = localStorage.getItem(USER_KEY); return u ? JSON.parse(u) : null; },
  setTokens(access, refresh, user) {
    if (access) localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  },
  isAuthenticated() { return !!this.getToken(); },

  // --- Auth helpers ---
  _headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    const token = this.getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  },

  async _fetchWithAuth(url, options = {}) {
    const res = await fetch(url, { ...options, headers: this._headers(options.headers) });
    if (res.status === 401) {
      const refreshed = await this._tryRefresh();
      if (refreshed) {
        const retry = await fetch(url, { ...options, headers: this._headers(options.headers) });
        return retry;
      }
      this.clearTokens();
      window.dispatchEvent(new CustomEvent('auth:logout'));
      throw new Error('Session expired');
    }
    return res;
  },

  async _tryRefresh() {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;
    try {
      const res = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setTokens(data.access_token, null, null);
      return true;
    } catch { return false; }
  },

  // --- Auth API ---
  async login(username, password) {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Login failed'); }
    const data = await res.json();
    this.setTokens(data.access_token, data.refresh_token, data.user);
    return data;
  },

  async register(username, password, email = '') {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, email }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Registration failed'); }
    const data = await res.json();
    this.setTokens(data.access_token, data.refresh_token, data.user);
    return data;
  },

  async logout() {
    try {
      await fetch('/api/v1/auth/logout', { method: 'POST', headers: this._headers() });
    } catch {}
    this.clearTokens();
  },

  async checkAuth() {
    const token = this.getToken();
    if (!token) return { authenticated: false };
    try {
      const res = await fetch('/api/v1/auth/status', { headers: this._headers() });
      if (!res.ok) { this.clearTokens(); return { authenticated: false }; }
      return res.json();
    } catch { return { authenticated: false }; }
  },

  // --- Wrapped methods with auth headers ---
  async query(payload) {
    const res = await this._fetchWithAuth('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail?.[0]?.msg || err.message || 'API error'); }
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

  async _fetch(url, key, ttl = 30000) {
    const now = Date.now();
    if (this._cache[key] && now - this._cache[key].ts < ttl) return this._cache[key].data;
    if (this._pending[key]) return this._pending[key].then(r => r || this._cache[key]?.data || null);
    this._pending[key] = (async () => {
      try {
        const res = await this._fetchWithAuth(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this._cache[key] = { data, ts: Date.now() };
        return data;
      } catch (e) {
        console.warn(`API ${key} failed:`, e.message);
        return this._cache[key]?.data || null;
      } finally {
        delete this._pending[key];
      }
    })();
    return this._pending[key];
  },

  getIndices() { return this._fetch('/api/v1/market/indices', 'indices', 60000); },
  getStocks() { return this._fetch('/api/v1/market/stocks', 'stocks', 60000); },
  getStock(ticker) { return this._fetch(`/api/v1/market/stocks/${ticker}`, `stock_${ticker}`, 30000); },
  getForex() { return this._fetch('/api/v1/market/forex', 'forex', 60000); },
  getCrypto() { return this._fetch('/api/v1/market/crypto', 'crypto', 30000); },
  getCommodities() { return this._fetch('/api/v1/market/commodities', 'commodities', 60000); },
  getBonds() { return this._fetch('/api/v1/market/bonds', 'bonds', 60000); },
  getMovers() { return this._fetch('/api/v1/market/movers', 'movers', 60000); },
  getNews() { return this._fetch('/api/v1/market/news', 'news', 120000); },

  getAccounts() { return this._fetch('/api/v1/banking/accounts', 'banking_accounts', 30000); },
  getAccountSummary() { return this._fetch('/api/v1/banking/accounts/summary', 'banking_summary', 30000); },
  getTransfers() { return this._fetch('/api/v1/banking/transfers', 'banking_transfers', 30000); },
  getLoans() { return this._fetch('/api/v1/banking/loans', 'banking_loans', 30000); },
  getDeposits() { return this._fetch('/api/v1/banking/deposits', 'banking_deposits', 30000); },
  getCreditCards() { return this._fetch('/api/v1/banking/cards', 'banking_cards', 30000); },
  getBills() { return this._fetch('/api/v1/banking/bills', 'banking_bills', 30000); },

  getPayments() { return this._fetch('/api/v1/payments/', 'payments', 30000); },
  getSwiftBanks() { return this._fetch('/api/v1/payments/swift/banks', 'swift_banks', 60000); },
  getSepaMandates() { return this._fetch('/api/v1/payments/sepa/mandates', 'sepa_mandates', 60000); },
  getAchRoutes() { return this._fetch('/api/v1/payments/ach/routes', 'ach_routes', 60000); },
  getFasterPayments() { return this._fetch('/api/v1/payments/faster/limits', 'faster_limits', 60000); },
  getPaymentRails() { return this._fetch('/api/v1/payments/rails', 'payment_rails', 60000); },

  getBankingWallets() { return this._fetch('/api/v1/wallets/banking', 'wallets_banking', 30000); },
  getCryptoWallets() { return this._fetch('/api/v1/wallets/crypto', 'wallets_crypto', 30000); },
  getInsuranceWallets() { return this._fetch('/api/v1/wallets/insurance', 'wallets_insurance', 30000); },

  getComplianceCountries() { return this._fetch('/api/v1/compliance/countries', 'compliance_countries', 60000); },
  getComplianceScore(userId) { return this._fetch(`/api/v1/compliance/score?user_id=${userId}`, `compliance_score_${userId}`, 30000); },

  getWafStats() { return this._fetch('/api/v1/security/waf/stats', 'waf_stats', 15000); },
  getIdsEvents() { return this._fetch('/api/v1/security/ids/events', 'ids_events', 15000); },
  getSiemLogs() { return this._fetch('/api/v1/security/siem/logs', 'siem_logs', 15000); },
  getDdosStats() { return this._fetch('/api/v1/security/ddos/stats', 'ddos_stats', 15000); },

  getDataSource() { return this._fetch('/api/v1/config/data-source', 'datasource', 15000); },
  async toggleDataSource() {
    const res = await this._fetchWithAuth('/api/v1/config/data-source/toggle', { method: 'POST' });
    return res.json();
  },
  async setDataSource(mode) {
    const res = await this._fetchWithAuth('/api/v1/config/data-source', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
    return res.json();
  },

  getInsurancePolicies() { return this._fetch('/api/v1/insurance/policies', 'insurance_policies', 30000); },
  getInsuranceClaims() { return this._fetch('/api/v1/insurance/claims', 'insurance_claims', 30000); },
  getInsurancePremiums() { return this._fetch('/api/v1/insurance/premiums', 'insurance_premiums', 30000); },

  getInsights(section) { return this._fetch(`/api/v1/insights/${section}`, `insights_${section}`, 120000); },
};
