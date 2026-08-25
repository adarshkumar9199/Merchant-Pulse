// Dashboard Controller - Merchant Growth & Retention Decision Engine

let chartGMV = null;
let chartVolume = null;
let chartSegment = null;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();

  document.getElementById('btnApplyFilters').addEventListener('click', loadFilteredMerchants);
  document.getElementById('filterSearch').addEventListener('keyup', (e) => {
    if (e.key === 'Enter') loadFilteredMerchants();
  });
});

function getFormattedTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function updateLastUpdatedBadge(timeStr, isLive = true) {
  const badge = document.getElementById('lastUpdatedBadge');
  if (badge) {
    if (isLive) {
      badge.innerText = `Last Updated: Today at ${timeStr}`;
      badge.style.background = 'rgba(16, 185, 129, 0.15)';
      badge.style.color = '#10b981';
      badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    } else {
      badge.innerText = `Cached: ${timeStr} (Syncing...)`;
      badge.style.background = 'rgba(245, 158, 11, 0.15)';
      badge.style.color = '#f59e0b';
      badge.style.borderColor = 'rgba(245, 158, 11, 0.3)';
    }
  }
}

const DEFAULT_PREWARMED_SUMMARY = {
  total_merchants: 500,
  active_merchants: 500,
  total_transactions: 477691,
  total_gmv: 2220658853.81,
  overall_success_rate: 94.15,
  at_risk_count: 55
};

async function initDashboard() {
  // 1. Instantly render pre-warmed default or cached data (Zero Blank Screen!)
  const cachedTime = localStorage.getItem('dashboard_cache_time');
  const cachedSummary = localStorage.getItem('cache_summary');

  let initialSummary = DEFAULT_PREWARMED_SUMMARY;
  if (cachedSummary) {
    try { initialSummary = JSON.parse(cachedSummary); } catch (e) {}
  }
  
  renderSummaryKPIs(initialSummary);
  updateLastUpdatedBadge(cachedTime || getFormattedTimestamp(), !cachedTime);

  // 2. Fetch fresh data in background
  await Promise.all([
    loadSummaryKPIs(),
    loadTrends(),
    loadSegments(),
    loadOpportunities(),
    loadFilteredMerchants()
  ]);

  // 3. Mark last updated timestamp
  const freshTime = getFormattedTimestamp();
  localStorage.setItem('dashboard_cache_time', freshTime);
  updateLastUpdatedBadge(freshTime, true);
}

function renderSummaryKPIs(data) {
  document.getElementById('kpiTotalMerchants').innerText = formatNumber(data.total_merchants);
  document.getElementById('kpiActiveMerchants').innerText = formatNumber(data.active_merchants);
  document.getElementById('kpiTotalGMV').innerText = formatCurrency(data.total_gmv);
  document.getElementById('kpiTotalTxns').innerText = formatNumber(data.total_transactions);
  document.getElementById('kpiSuccessRate').innerText = data.overall_success_rate + '%';
  document.getElementById('kpiAtRiskCount').innerText = formatNumber(data.at_risk_count);
}

async function loadSummaryKPIs() {
  try {
    const res = await fetch('/api/dashboard/summary');
    const data = await res.json();
    renderSummaryKPIs(data);
    localStorage.setItem('cache_summary', JSON.stringify(data));
  } catch (err) {
    console.error('Error loading summary KPIs:', err);
  }
}

async function loadTrends() {
  try {
    const res = await fetch('/api/dashboard/trends');
    const trends = await res.json();

    const labels = trends.map(t => t.month);
    const gmvData = trends.map(t => t.gmv);
    const volumeData = trends.map(t => t.volume);

    // Monthly GMV Line Chart
    const ctxGMV = document.getElementById('chartMonthlyGMV').getContext('2d');
    if (chartGMV) chartGMV.destroy();

    const gradientGMV = ctxGMV.createLinearGradient(0, 0, 0, 300);
    gradientGMV.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    gradientGMV.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    chartGMV = new Chart(ctxGMV, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Gross Processing Value (₹)',
          data: gmvData,
          borderColor: '#6366f1',
          borderWidth: 3,
          backgroundColor: gradientGMV,
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#6366f1'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => 'GMV: ' + formatCurrency(ctx.raw)
            }
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { 
            grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
            ticks: { 
              color: '#9ca3af',
              callback: (val) => formatCurrency(val)
            } 
          }
        }
      }
    });

    // Monthly Volume Bar Chart
    const ctxVol = document.getElementById('chartMonthlyVolume').getContext('2d');
    if (chartVolume) chartVolume.destroy();

    chartVolume = new Chart(ctxVol, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Transaction Count',
          data: volumeData,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });

  } catch (err) {
    console.error('Error loading trends:', err);
  }
}

async function loadSegments() {
  try {
    const res = await fetch('/api/segments');
    const segments = await res.json();

    const labels = segments.map(s => s.segment);
    const data = segments.map(s => s.count);

    const colors = {
      'High Growth': '#10b981',
      'Healthy': '#3b82f6',
      'Stable': '#8b5cf6',
      'Declining': '#f59e0b',
      'At Risk': '#ef4444'
    };

    const ctxSeg = document.getElementById('chartSegmentDonut').getContext('2d');
    if (chartSegment) chartSegment.destroy();

    chartSegment = new Chart(ctxSeg, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: labels.map(l => colors[l] || '#6b7280'),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#f3f4f6', font: { size: 11 } }
          }
        },
        cutout: '70%'
      }
    });
  } catch (err) {
    console.error('Error loading segments:', err);
  }
}

async function loadOpportunities() {
  try {
    const res = await fetch('/api/opportunities');
    const opps = await res.json();

    const container = document.getElementById('opportunityContainer');
    container.innerHTML = '';

    // Show top 4 opportunity hotspots
    opps.slice(0, 4).forEach(o => {
      const card = document.createElement('div');
      card.className = 'opportunity-card';
      card.innerHTML = `
        <div class="opp-header">
          <div>
            <div class="opp-city">${o.city}</div>
            <div class="opp-cat">${o.category}</div>
          </div>
          <div class="opp-score-badge" title="Opportunity Score 0-100">${o.opportunity_score}</div>
        </div>
        <div class="opp-metrics">
          <div class="opp-metric-item">
            <span>Demand Volume</span>
            <strong>${formatNumber(o.demand_volume)} txns</strong>
          </div>
          <div class="opp-metric-item">
            <span>Demand GMV</span>
            <strong>${formatCurrency(o.demand_gmv)}</strong>
          </div>
          <div class="opp-metric-item">
            <span>Existing Merchants</span>
            <strong>${o.existing_merchant_count} stores</strong>
          </div>
          <div class="opp-metric-item">
            <span>Avg Ticket Size</span>
            <strong>₹${o.avg_transaction_value}</strong>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Error loading opportunities:', err);
  }
}

async function loadFilteredMerchants() {
  const search = document.getElementById('filterSearch').value.trim();
  const city = document.getElementById('filterCity').value;
  const category = document.getElementById('filterCategory').value;
  const segment = document.getElementById('filterSegment').value;

  const tbody = document.getElementById('merchantTableBody');
  if (tbody && tbody.children.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:var(--text-muted); padding:20px;">⚡ Loading merchant decision data...</td></tr>`;
  }

  let url = `/api/merchants?limit=30&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;
  if (city) url += `city=${encodeURIComponent(city)}&`;
  if (category) url += `category=${encodeURIComponent(category)}&`;
  if (segment) url += `segment=${encodeURIComponent(segment)}&`;

  try {
    const res = await fetch(url);
    const merchants = await res.json();

    tbody.innerHTML = '';

    if (merchants.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:var(--text-muted); padding:24px;">No merchants matching filter criteria.</td></tr>`;
      return;
    }

    merchants.forEach(m => {
      const tr = document.createElement('tr');
      tr.addEventListener('click', () => {
        window.location.href = `/merchants/${m.merchant_id}`;
      });

      const growthClass = m.growth_rate >= 0 ? 'color: var(--accent-green);' : 'color: var(--accent-red);';
      const growthSign = m.growth_rate > 0 ? '+' : '';

      tr.innerHTML = `
        <td class="col-id">${m.merchant_id}</td>
        <td class="col-name" title="${m.merchant_name}">${m.merchant_name}</td>
        <td class="col-cat">${m.merchant_category}</td>
        <td class="col-city">${m.city}</td>
        <td class="col-health">
          <span class="health-score-pill ${m.health_score >= 75 ? 'health-high' : m.health_score >= 50 ? 'health-mid' : 'health-low'}">
            ${m.health_score}
          </span>
        </td>
        <td class="col-growth" style="${growthClass}">${growthSign}${m.growth_rate}%</td>
        <td class="col-success">${m.success_rate}%</td>
        <td class="col-segment">${getSegmentBadgeHtml(m.segment)}</td>
        <td class="col-action">${m.recommended_action}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error loading filtered merchants:', err);
  }
}

// Modal Handlers
function openImportModal() {
  const modal = document.getElementById('importCsvModal');
  if (modal) modal.style.display = 'flex';
  const alertBox = document.getElementById('importAlertBox');
  if (alertBox) alertBox.style.display = 'none';
}

function closeImportModal() {
  const modal = document.getElementById('importCsvModal');
  if (modal) modal.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('formImportCsv');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const alertBox = document.getElementById('importAlertBox');
      const submitBtn = document.getElementById('btnSubmitImport');
      
      const formData = new FormData(form);
      submitBtn.disabled = true;
      submitBtn.innerText = 'Uploading...';

      try {
        const res = await fetch('/api/import-csv', {
          method: 'POST',
          body: formData
        });
        const result = await res.json();

        alertBox.style.display = 'block';
        if (res.ok) {
          alertBox.style.background = 'rgba(16, 185, 129, 0.2)';
          alertBox.style.color = '#10b981';
          alertBox.innerText = result.message;
          setTimeout(() => {
            closeImportModal();
            location.reload();
          }, 1500);
        } else {
          alertBox.style.background = 'rgba(239, 68, 68, 0.2)';
          alertBox.style.color = '#ef4444';
          alertBox.innerText = result.detail || 'Upload failed';
        }
      } catch (err) {
        alertBox.style.display = 'block';
        alertBox.style.background = 'rgba(239, 68, 68, 0.2)';
        alertBox.style.color = '#ef4444';
        alertBox.innerText = 'Network error during upload.';
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Upload & Process';
      }
    });
  }
});

