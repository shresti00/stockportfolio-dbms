// Stock Portfolio Tracker & Wealth Platform Frontend Engine

let currentUserId = 1;
let currentUsername = 'dale_cooper';
let allAssets = [];
let allSchemes = [];

let capChartInstance = null;
let sectorChartInstance = null;
let maChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
  await initApp();
});

async function initApp() {
  await loadUsers();
  await checkDbStatus();
  await loadAssetsAndSchemes();
  await refreshCurrentView();
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  const msgEl = document.getElementById('toast-message');
  const iconEl = document.getElementById('toast-icon');

  msgEl.innerText = message;
  iconEl.className = isError
    ? 'fa-solid fa-circle-exclamation text-rose-400'
    : 'fa-solid fa-circle-check text-emerald-400';

  toast.classList.remove('translate-y-20', 'opacity-0');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 3500);
}

function switchTab(tabId) {
  const tabs = [
    'dashboard', 'explorer', 'stock-portfolio',
    'transactions', 'watchlist', 'mutual-funds',
    'my-funds', 'exposure', 'corporate'
  ];
  tabs.forEach(t => {
    const sec = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`nav-${t}`);
    if (t === tabId) {
      if (sec) sec.classList.remove('hidden');
      if (btn) btn.className = 'nav-active px-3.5 py-2 rounded-lg transition flex items-center gap-2';
    } else {
      if (sec) sec.classList.add('hidden');
      if (btn) btn.className = 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 px-3.5 py-2 rounded-lg transition flex items-center gap-2';
    }
  });
}

// 1. Users Switcher
async function loadUsers() {
  try {
    const res = await fetch('/api/users');
    const users = await res.json();
    const sel = document.getElementById('active-user-select');
    sel.innerHTML = users.map(u => `
      <option value="${u.user_id}" ${u.user_id === currentUserId ? 'selected' : ''}>
        ${u.username} (ID: ${u.user_id})
      </option>
    `).join('');
  } catch (e) {
    console.error('Error loading users', e);
  }
}

async function handleUserChange() {
  const sel = document.getElementById('active-user-select');
  currentUserId = parseInt(sel.value);
  currentUsername = sel.options[sel.selectedIndex].text.split(' ')[0];
  showToast(`Switched investor profile to: ${currentUsername}`);
  await refreshCurrentView();
}

async function checkDbStatus() {
  try {
    const res = await fetch('/api/status');
    const status = await res.json();
    const textEl = document.getElementById('db-status-text');
    const pill = document.getElementById('db-status-pill');

    if (status.mode === 'AWS_RDS_MYSQL') {
      textEl.innerText = `AWS RDS MySQL (${status.database})`;
      pill.className = 'hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200';
    } else {
      textEl.innerText = `Local DBMS Replica`;
      pill.className = 'hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200';
    }
  } catch (e) {
    console.error('Error fetching DB status', e);
  }
}

async function loadAssetsAndSchemes() {
  try {
    const [resAssets, resFunds] = await Promise.all([
      fetch('/api/assets'),
      fetch('/api/funds')
    ]);
    allAssets = await resAssets.json();
    const fundsData = await resFunds.json();
    allSchemes = fundsData.schemes || [];

    // Populate modal dropdowns & watchlist dropdowns
    const wlSel = document.getElementById('wl-ticker-select');
    if (wlSel) {
      wlSel.innerHTML = allAssets.map(a => `<option value="${a.ticker}">${a.ticker} - ${a.company_name}</option>`).join('');
    }

    const tradeSel = document.getElementById('modal-trade-ticker');
    if (tradeSel) {
      tradeSel.innerHTML = allAssets.map(a => `<option value="${a.ticker}">${a.ticker} (${a.company_name})</option>`).join('');
    }

    const maSel = document.getElementById('select-ma-stock');
    if (maSel) {
      maSel.innerHTML = allAssets.map(a => `<option value="${a.ticker}">${a.ticker} - ${a.company_name}</option>`).join('');
    }

    const invSel = document.getElementById('modal-invest-scheme');
    if (invSel) {
      invSel.innerHTML = allSchemes.map(s => `<option value="${s.scheme_id}">${s.scheme_nm} (${s.fund_house_nm})</option>`).join('');
    }
  } catch (e) {
    console.error('Error loading assets/schemes', e);
  }
}

async function refreshCurrentView() {
  await Promise.all([
    loadDashboard(),
    loadStocksExplorer(),
    loadTransactions(),
    loadWatchlist(),
    loadMutualFunds(),
    loadExposure(),
    loadCorporateOwnership(),
    loadStockTrendline()
  ]);
}

async function refreshData() {
  await refreshCurrentView();
  showToast('Live portfolio synchronized');
}

// ================= 2. DASHBOARD & PORTFOLIO OVERVIEW ================= //
async function loadDashboard() {
  try {
    const res = await fetch(`/api/portfolio/user/${currentUserId}`);
    const data = await res.json();

    // Stats
    document.getElementById('stat-direct-value').innerText = `₹${parseFloat(data.direct_stock_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('stat-invested-capital').innerText = `₹${parseFloat(data.direct_invested_capital || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('stat-mf-value').innerText = `₹${parseFloat(data.mf_invested_total || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

    const uPnl = parseFloat(data.total_unrealized_pnl || 0);
    const rPnl = parseFloat(data.total_realized_pnl || 0);

    const uEl = document.getElementById('stat-unrealized-pnl');
    uEl.innerText = `${uPnl >= 0 ? '+' : ''}₹${uPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    uEl.className = `text-xl font-bold ${uPnl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`;

    const rEl = document.getElementById('stat-realized-pnl');
    rEl.innerText = `${rPnl >= 0 ? '+' : ''}₹${rPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    rEl.className = `font-semibold ${rPnl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`;

    // Target Alert Banner
    const banner = document.getElementById('dashboard-alerts-banner');
    const bannerText = document.getElementById('dashboard-alerts-text');
    if (data.alerts && data.alerts.length > 0) {
      banner.classList.remove('hidden');
      const tickers = data.alerts.map(a => a.ticker).join(', ');
      bannerText.innerText = `Target price hit for: ${tickers}. Ready for review.`;
    } else {
      banner.classList.add('hidden');
    }

    // Allocation Charts
    renderCapChart(data.cap_allocation || []);
    renderSectorChart(data.sector_allocation || []);

    // Holdings Tables
    renderHoldingsTable(data.active_holdings || []);

  } catch (e) {
    console.error('Error loading dashboard', e);
  }
}

function renderHoldingsTable(holdings) {
  const dashTbody = document.getElementById('dashboard-holdings-tbody');
  const portTbody = document.getElementById('portfolio-detailed-tbody');

  if (holdings.length === 0) {
    const emptyRow = `<tr><td colspan="8" class="py-6 text-center text-slate-400">No active stock positions held. Use "Record Trade" to start investing.</td></tr>`;
    dashTbody.innerHTML = emptyRow;
    portTbody.innerHTML = emptyRow;
    return;
  }

  const rowsHtml = holdings.map(h => {
    const netQty = parseFloat(h.net_qty || 0);
    const avgBuy = parseFloat(h.avg_buy_price || 0);
    const currPrice = parseFloat(h.current_price || 0);
    const curVal = netQty * currPrice;
    const uPnl = parseFloat(h.unrealized_gain || 0);
    const rPnl = parseFloat(h.realized_gain || 0);

    return `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-3 px-4 font-bold text-slate-900">${h.ticker}</td>
        <td class="py-3 px-4 font-semibold">${netQty.toFixed(2)}</td>
        <td class="py-3 px-4 text-slate-600">₹${avgBuy.toFixed(2)}</td>
        <td class="py-3 px-4 text-slate-800">₹${currPrice.toFixed(2)}</td>
        <td class="py-3 px-4 font-bold text-slate-900">₹${curVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
        <td class="py-3 px-4">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${rPnl >= 0 ? 'badge-profit' : 'badge-loss'}">
            ${rPnl >= 0 ? '+' : ''}₹${rPnl.toFixed(2)}
          </span>
        </td>
        <td class="py-3 px-4">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${uPnl >= 0 ? 'badge-profit' : 'badge-loss'}">
            ${uPnl >= 0 ? '+' : ''}₹${uPnl.toFixed(2)}
          </span>
        </td>
        <td class="py-3 px-4 text-right">
          <button onclick="prefillTradeModal('${h.ticker}', 'SELL', ${netQty}, ${currPrice})" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-2.5 py-1 rounded-md transition">
            Sell
          </button>
        </td>
      </tr>
    `;
  }).join('');

  dashTbody.innerHTML = rowsHtml;
  portTbody.innerHTML = rowsHtml;
}

function renderCapChart(capAlloc) {
  const ctx = document.getElementById('capChart').getContext('2d');
  const labels = capAlloc.map(c => c.cap_category);
  const values = capAlloc.map(c => parseFloat(c.invested) || 0);

  if (capChartInstance) capChartInstance.destroy();
  capChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: ['#2563eb', '#10b981', '#f59e0b'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
    }
  });
}

function renderSectorChart(sectorAlloc) {
  const ctx = document.getElementById('sectorChart').getContext('2d');
  const labels = sectorAlloc.map(s => s.sector);
  const values = sectorAlloc.map(s => parseFloat(s.net_invested) || 0);

  if (sectorChartInstance) sectorChartInstance.destroy();
  sectorChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Net Invested (₹)',
        data: values,
        backgroundColor: '#6366f1',
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
      }
    }
  });
}

// ================= 3. EXPLORE STOCKS ================= //
async function loadStocksExplorer() {
  try {
    const res = await fetch('/api/stocks/explorer');
    const data = await res.json();

    const assets = data.assets || [];
    const perfMap = {};
    (data.performance || []).forEach(p => { perfMap[p.ticker] = p.prct_change; });
    const rangeMap = {};
    (data.price_ranges || []).forEach(r => { rangeMap[r.ticker] = r; });
    const volMap = {};
    (data.volatility || []).forEach(v => { volMap[v.ticker] = v.volatility; });
    const dayMap = {};
    (data.latest_day_change || []).forEach(l => { dayMap[l.ticker] = l.day_change_pct; });

    const tbody = document.getElementById('explorer-stocks-tbody');
    tbody.innerHTML = assets.map(a => {
      const ticker = a.ticker;
      const dayChg = dayMap[ticker] !== undefined ? parseFloat(dayMap[ticker]) : 0;
      const yrChg = perfMap[ticker] !== undefined ? parseFloat(perfMap[ticker]) : 0;
      const v = volMap[ticker] !== undefined ? parseFloat(volMap[ticker]) : 0;
      const r = rangeMap[ticker] || { low: 0, high: 0, price_range: 0 };

      return `
        <tr class="hover:bg-slate-50/80 transition" data-ticker="${ticker}" data-name="${a.company_name.toLowerCase()}">
          <td class="py-3 px-4 font-bold text-slate-900">
            <div>${ticker}</div>
            <div class="text-xs font-normal text-slate-500">${a.company_name}</div>
          </td>
          <td class="py-3 px-4 text-slate-600">${a.sector}</td>
          <td class="py-3 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700">
              ${a.cap_category}
            </span>
          </td>
          <td class="py-3 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${dayChg >= 0 ? 'badge-profit' : 'badge-loss'}">
              ${dayChg >= 0 ? '+' : ''}${dayChg.toFixed(2)}%
            </span>
          </td>
          <td class="py-3 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${yrChg >= 0 ? 'badge-profit' : 'badge-loss'}">
              ${yrChg >= 0 ? '+' : ''}${yrChg.toFixed(2)}%
            </span>
          </td>
          <td class="py-3 px-4 font-mono text-slate-700">${v.toFixed(2)}</td>
          <td class="py-3 px-4 text-xs text-slate-600">₹${parseFloat(r.low).toFixed(2)} - ₹${parseFloat(r.high).toFixed(2)}</td>
          <td class="py-3 px-4 text-right space-x-1">
            <button onclick="prefillTradeModal('${ticker}', 'BUY')" class="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold px-2.5 py-1 rounded transition">
              Buy
            </button>
            <button onclick="addToWatchlistQuick('${ticker}')" class="text-xs bg-slate-100 text-slate-600 hover:bg-slate-200 font-semibold px-2 py-1 rounded transition" title="Add to Watchlist">
              <i class="fa-regular fa-bell"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error('Error loading stocks explorer', e);
  }
}

function filterStocksTable() {
  const query = document.getElementById('stock-search').value.toLowerCase();
  const rows = document.querySelectorAll('#explorer-stocks-tbody tr');
  rows.forEach(r => {
    const ticker = r.getAttribute('data-ticker').toLowerCase();
    const name = r.getAttribute('data-name');
    if (ticker.includes(query) || name.includes(query)) {
      r.classList.remove('hidden');
    } else {
      r.classList.add('hidden');
    }
  });
}

async function loadStockTrendline() {
  const sel = document.getElementById('select-ma-stock');
  if (!sel || !sel.value) return;
  const ticker = sel.value;

  try {
    const res = await fetch(`/api/stocks/${ticker}`);
    const data = await res.json();
    const history = (data.history || []).reverse();

    const dates = history.map(h => h.price_date);
    const closePrices = history.map(h => parseFloat(h.close_price));
    const ma7 = history.map(h => parseFloat(h.ma_7));
    const ma30 = history.map(h => parseFloat(h.ma_30));

    const ctx = document.getElementById('maChart').getContext('2d');
    if (maChartInstance) maChartInstance.destroy();

    maChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: `${ticker} Daily Close`,
            data: closePrices,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.05)',
            fill: true,
            tension: 0.2
          },
          {
            label: '7-Day Moving Avg',
            data: ma7,
            borderColor: '#10b981',
            borderDash: [5, 5],
            fill: false,
            tension: 0.2
          },
          {
            label: '30-Day Moving Avg',
            data: ma30,
            borderColor: '#f59e0b',
            fill: false,
            tension: 0.2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { grid: { color: '#f1f5f9' } },
          x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }
        }
      }
    });
  } catch (e) {
    console.error('Error loading trendline', e);
  }
}

// ================= 4. TRANSACTIONS & MODAL ================= //
async function loadTransactions() {
  try {
    const res = await fetch(`/api/transactions?user_id=${currentUserId}`);
    const txns = await res.json();
    const tbody = document.getElementById('txn-ledger-tbody');

    if (txns.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-400">No recorded transactions for ${currentUsername}.</td></tr>`;
      return;
    }

    tbody.innerHTML = txns.map(t => `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-3 px-4 font-mono text-xs text-slate-400">#${t.transaction_id}</td>
        <td class="py-3 px-4 font-bold text-slate-900">${t.ticker}</td>
        <td class="py-3 px-4">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold ${t.txn_type === 'BUY' ? 'badge-profit' : 'badge-loss'}">
            ${t.txn_type}
          </span>
        </td>
        <td class="py-3 px-4 font-medium">${parseFloat(t.quantity).toFixed(2)}</td>
        <td class="py-3 px-4">₹${parseFloat(t.price_per_share).toFixed(2)}</td>
        <td class="py-3 px-4 font-bold text-slate-900">₹${parseFloat(t.total_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
        <td class="py-3 px-4 text-xs text-slate-500">${t.txn_date}</td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Error loading transactions', e);
  }
}

function openTradeModal(action = 'BUY') {
  document.getElementById('modal-trade-action').value = action;
  updateModalPrice();
  document.getElementById('trade-modal').classList.remove('hidden');
}

function closeTradeModal() {
  document.getElementById('trade-modal').classList.add('hidden');
}

function prefillTradeModal(ticker, action = 'BUY', maxQty = null, price = null) {
  const sel = document.getElementById('modal-trade-ticker');
  sel.value = ticker;
  document.getElementById('modal-trade-action').value = action;
  if (price) {
    document.getElementById('modal-trade-price').value = price;
  } else {
    updateModalPrice();
  }
  if (maxQty && action === 'SELL') {
    document.getElementById('modal-trade-qty').value = maxQty;
  }
  document.getElementById('trade-modal').classList.remove('hidden');
}

function updateModalPrice() {
  const ticker = document.getElementById('modal-trade-ticker').value;
  const match = allAssets.find(a => a.ticker === ticker);
  if (match && match.latest_price) {
    document.getElementById('modal-trade-price').value = match.latest_price;
  }
}

async function handleTradeSubmit(e) {
  e.preventDefault();
  const payload = {
    user_id: currentUserId,
    ticker: document.getElementById('modal-trade-ticker').value,
    txn_type: document.getElementById('modal-trade-action').value,
    quantity: parseFloat(document.getElementById('modal-trade-qty').value),
    price_per_share: parseFloat(document.getElementById('modal-trade-price').value)
  };

  try {
    const res = await fetch('/api/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Trade execution failed');

    showToast(result.message);
    closeTradeModal();
    document.getElementById('modal-trade-qty').value = '';
    await loadDashboard();
    await loadTransactions();
    await loadExposure();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ================= 5. WATCHLIST & ALERTS ================= //
async function loadWatchlist() {
  try {
    const res = await fetch(`/api/watchlist?user_id=${currentUserId}`);
    const data = await res.json();

    const targetsReached = data.targets_reached || [];
    const items = data.items || [];
    const unowned = data.unowned || [];

    // Alerts
    const alertsContainer = document.getElementById('target-alerts-container');
    if (targetsReached.length === 0) {
      alertsContainer.innerHTML = `<div class="col-span-3 text-xs text-slate-500 py-1">No tracked stocks are currently trading at or above your target price.</div>`;
    } else {
      alertsContainer.innerHTML = targetsReached.map(t => `
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center justify-between">
          <div>
            <div class="text-sm font-bold text-slate-900">${t.ticker}</div>
            <div class="text-xs text-slate-500">Target: ₹${parseFloat(t.target_price).toFixed(2)}</div>
          </div>
          <div class="text-right">
            <span class="text-xs font-bold text-emerald-600">₹${parseFloat(t.current_price).toFixed(2)}</span>
            <button onclick="prefillTradeModal('${t.ticker}', 'BUY')" class="block text-xs bg-amber-600 hover:bg-amber-700 text-white font-semibold px-2 py-0.5 rounded mt-1 transition">
              Trade
            </button>
          </div>
        </div>
      `).join('');
    }

    // Complete Watchlist
    const tbody = document.getElementById('watchlist-table-tbody');
    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-400">Watchlist is empty. Add stocks above.</td></tr>`;
    } else {
      tbody.innerHTML = items.map(w => {
        const cur = parseFloat(w.current_price || 0);
        const tgt = parseFloat(w.target_price || 0);
        const reached = cur >= tgt;
        return `
          <tr class="hover:bg-slate-50/80 transition">
            <td class="py-3 px-3 font-bold text-slate-900">${w.ticker}</td>
            <td class="py-3 px-3 text-slate-600">₹${tgt.toFixed(2)}</td>
            <td class="py-3 px-3 font-semibold text-slate-800">₹${cur.toFixed(2)}</td>
            <td class="py-3 px-3">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${reached ? 'badge-profit' : 'bg-slate-100 text-slate-600'}">
                ${reached ? 'Target Met' : 'Tracking'}
              </span>
            </td>
            <td class="py-3 px-3 text-right">
              <button onclick="deleteWatchlist(${w.watchlist_id})" class="text-slate-400 hover:text-rose-600 transition" title="Remove">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    // Unowned Watchlist
    const unownedTbody = document.getElementById('unowned-tbody');
    if (unowned.length === 0) {
      unownedTbody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-slate-400">All watchlisted stocks are currently owned!</td></tr>`;
    } else {
      unownedTbody.innerHTML = unowned.map(u => `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-3 font-bold text-slate-900">${u.ticker}</td>
          <td class="py-3 px-3 text-slate-600">₹${parseFloat(u.target_price).toFixed(2)}</td>
          <td class="py-3 px-3 text-right">
            <button onclick="prefillTradeModal('${u.ticker}', 'BUY')" class="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold px-2 py-0.5 rounded transition">
              Buy
            </button>
          </td>
        </tr>
      `).join('');
    }

  } catch (e) {
    console.error('Error loading watchlist', e);
  }
}

async function handleWatchlistSubmit(e) {
  e.preventDefault();
  const payload = {
    user_id: currentUserId,
    ticker: document.getElementById('wl-ticker-select').value,
    target_price: parseFloat(document.getElementById('wl-target-input').value)
  };

  try {
    const res = await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Could not add to watchlist');

    showToast(result.message);
    document.getElementById('wl-target-input').value = '';
    await loadWatchlist();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function addToWatchlistQuick(ticker) {
  const match = allAssets.find(a => a.ticker === ticker);
  const target = match && match.latest_price ? (parseFloat(match.latest_price) * 1.05).toFixed(2) : 1000;
  const payload = { user_id: currentUserId, ticker: ticker, target_price: parseFloat(target) };

  try {
    const res = await fetch('/api/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Failed to add');
    showToast(`Added ${ticker} to watchlist (Target: ₹${target})`);
    await loadWatchlist();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function deleteWatchlist(id) {
  try {
    await fetch(`/api/watchlist/${id}`, { method: 'DELETE' });
    showToast('Removed from watchlist');
    await loadWatchlist();
  } catch (e) {
    console.error('Error deleting watchlist item', e);
  }
}

// ================= 6. MUTUAL FUNDS & INVESTING ================= //
async function loadMutualFunds() {
  try {
    const res = await fetch('/api/funds');
    const data = await res.json();

    const schemes = data.schemes || [];
    const growthMap = {};
    (data.nav_growth || []).forEach(g => { growthMap[g.scheme_id] = g.growth_pct; });

    const tbody = document.getElementById('mf-schemes-tbody');
    tbody.innerHTML = schemes.map(s => {
      const g = growthMap[s.scheme_id] !== undefined ? parseFloat(growthMap[s.scheme_id]) : 0;
      return `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-4 font-bold text-slate-900">${s.scheme_nm}</td>
          <td class="py-3 px-4 text-slate-600">${s.fund_house_nm}</td>
          <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-xs bg-slate-100 font-semibold">${s.category}</span></td>
          <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-xs font-semibold ${s.risk_level === 'HIGH' ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}">${s.risk_level}</span></td>
          <td class="py-3 px-4 font-mono font-semibold">₹${parseFloat(s.nav).toFixed(4)}</td>
          <td class="py-3 px-4 font-bold ${g >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${g >= 0 ? '+' : ''}${g.toFixed(2)}%</td>
          <td class="py-3 px-4 text-slate-600">₹${parseFloat(s.min_investment).toFixed(2)}</td>
          <td class="py-3 px-4 text-right">
            <button onclick="prefillInvestModal(${s.scheme_id})" class="text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-3 py-1 rounded transition">
              Invest
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Holdings Breakdown
    const holdingsTbody = document.getElementById('scheme-holdings-tbody');
    holdingsTbody.innerHTML = (data.holdings || []).map(h => `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-3 px-4 font-semibold text-slate-900">${h.scheme_nm}</td>
        <td class="py-3 px-4 font-bold text-blue-600">${h.company_name} (${h.ticker})</td>
        <td class="py-3 px-4 text-slate-600">${h.sector}</td>
        <td class="py-3 px-4 font-semibold text-slate-900">${parseFloat(h.weight_pct).toFixed(2)}%</td>
      </tr>
    `).join('');

    // User's own scheme investments
    const myRes = await fetch(`/api/portfolio/user/${currentUserId}`);
    const myData = await myRes.json();
    const mySchemesTbody = document.getElementById('my-schemes-tbody');

    if (!myData.mf_investments || myData.mf_investments.length === 0) {
      mySchemesTbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-400">No mutual fund investments recorded for ${currentUsername}.</td></tr>`;
    } else {
      mySchemesTbody.innerHTML = myData.mf_investments.map(m => `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-4 font-bold text-slate-900">${m.scheme_nm}</td>
          <td class="py-3 px-4 text-slate-600">${m.fund_house_nm}</td>
          <td class="py-3 px-4 font-semibold">${parseFloat(m.units).toFixed(4)}</td>
          <td class="py-3 px-4">₹${parseFloat(m.nav_at_purchase).toFixed(4)}</td>
          <td class="py-3 px-4 font-semibold">₹${parseFloat(m.current_nav).toFixed(4)}</td>
          <td class="py-3 px-4 font-bold text-slate-900">₹${parseFloat(m.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
          <td class="py-3 px-4">
            <span class="px-2 py-0.5 rounded text-xs font-bold ${m.status === 'ACTIVE' ? 'badge-profit' : 'bg-slate-100 text-slate-600'}">
              ${m.status}
            </span>
          </td>
        </tr>
      `).join('');
    }

  } catch (e) {
    console.error('Error loading mutual funds', e);
  }
}

function openInvestModal() {
  updateMinInvestmentNotice();
  document.getElementById('invest-modal').classList.remove('hidden');
}

function closeInvestModal() {
  document.getElementById('invest-modal').classList.add('hidden');
}

function prefillInvestModal(schemeId) {
  document.getElementById('modal-invest-scheme').value = schemeId;
  updateMinInvestmentNotice();
  document.getElementById('invest-modal').classList.remove('hidden');
}

function updateMinInvestmentNotice() {
  const schemeId = parseInt(document.getElementById('modal-invest-scheme').value);
  const scheme = allSchemes.find(s => s.scheme_id === schemeId);
  const note = document.getElementById('modal-min-inv-text');
  if (scheme) {
    note.innerText = `Min. investment required: ₹${parseFloat(scheme.min_investment).toFixed(2)}`;
  }
}

async function handleInvestSubmit(e) {
  e.preventDefault();
  const payload = {
    user_id: currentUserId,
    scheme_id: parseInt(document.getElementById('modal-invest-scheme').value),
    amount: parseFloat(document.getElementById('modal-invest-amount').value),
    sip_amount: parseFloat(document.getElementById('modal-invest-sip').value) || null
  };

  try {
    const res = await fetch('/api/funds/invest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Investment failed');

    showToast(result.message);
    closeInvestModal();
    document.getElementById('modal-invest-amount').value = '';
    await loadDashboard();
    await loadMutualFunds();
    await loadExposure();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ================= 7. PORTFOLIO EXPOSURE & OVERLAP ================= //
async function loadExposure() {
  try {
    const res = await fetch(`/api/exposure/${currentUserId}`);
    const data = await res.json();

    // Overlap
    const overlapTbody = document.getElementById('overlap-tbody');
    const overlap = data.overlap || [];
    if (overlap.length === 0) {
      overlapTbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-slate-400">No overlap detected between your direct stocks and mutual fund holdings.</td></tr>`;
    } else {
      overlapTbody.innerHTML = overlap.map(o => `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-4 font-bold text-slate-900">${o.company_name} (${o.ticker})</td>
          <td class="py-3 px-4 font-semibold text-emerald-600">Directly Held</td>
          <td class="py-3 px-4 text-slate-700">${o.scheme_nm}</td>
          <td class="py-3 px-4 font-mono font-semibold">${parseFloat(o.weight_pct).toFixed(2)}%</td>
        </tr>
      `).join('');
    }

    // Indirect Exposure
    const indTbody = document.getElementById('indirect-exposure-tbody');
    const indirect = data.indirect_exposure || [];
    if (indirect.length === 0) {
      indTbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-400">No indirect exposures found. Invest in a scheme to establish exposure.</td></tr>`;
    } else {
      indTbody.innerHTML = indirect.map(i => `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="py-3 px-4 font-bold text-slate-900">${i.company_name} (${i.ticker})</td>
          <td class="py-3 px-4 text-slate-600">${i.sector}</td>
          <td class="py-3 px-4 text-slate-700">${i.scheme_nm}</td>
          <td class="py-3 px-4 font-semibold">${parseFloat(i.weight_pct).toFixed(2)}%</td>
          <td class="py-3 px-4 font-bold text-indigo-600">₹${parseFloat(i.estimated_exposure).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
        </tr>
      `).join('');
    }

  } catch (e) {
    console.error('Error loading exposure', e);
  }
}

// ================= 8. CORPORATE OWNERSHIP ================= //
async function loadCorporateOwnership() {
  try {
    const res = await fetch('/api/corporate-ownership');
    const data = await res.json();
    const tbody = document.getElementById('corporate-stakes-tbody');

    tbody.innerHTML = data.map(c => `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-3 px-4 font-bold text-slate-900">${c.investor}</td>
        <td class="py-3 px-4 font-semibold text-indigo-600">${c.investee}</td>
        <td class="py-3 px-4 font-bold text-slate-800">${parseFloat(c.stake_prct).toFixed(2)}%</td>
        <td class="py-3 px-4 font-mono text-slate-600">${parseInt(c.shares_held).toLocaleString('en-IN')} shares</td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Error loading corporate ownership', e);
  }
}
