// Merchant Profile Detail Controller

let chartDetailHistory = null;

document.addEventListener('DOMContentLoaded', () => {
  if (typeof MERCHANT_ID !== 'undefined' && MERCHANT_ID) {
    loadMerchantProfile(MERCHANT_ID);
  }
});

function formatCurrency(amt) {
  if (amt >= 10000000) return '₹' + (amt / 10000000).toFixed(2) + ' Cr';
  if (amt >= 100000) return '₹' + (amt / 100000).toFixed(2) + ' L';
  return '₹' + (amt || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function formatNumber(num) {
  return (num || 0).toLocaleString('en-IN');
}

function getSegmentBadgeHtml(segment) {
  switch (segment) {
    case 'High Growth': return `<span class="badge badge-high-growth" style="font-size:14px; padding:6px 14px;">🚀 High Growth</span>`;
    case 'Healthy': return `<span class="badge badge-healthy" style="font-size:14px; padding:6px 14px;">🟢 Healthy</span>`;
    case 'Stable': return `<span class="badge badge-stable" style="font-size:14px; padding:6px 14px;">🔵 Stable</span>`;
    case 'Declining': return `<span class="badge badge-declining" style="font-size:14px; padding:6px 14px;">🟡 Declining</span>`;
    case 'At Risk': return `<span class="badge badge-at-risk" style="font-size:14px; padding:6px 14px;">🔴 At Risk</span>`;
    default: return `<span class="badge badge-stable">${segment}</span>`;
  }
}

async function loadMerchantProfile(mId) {
  try {
    const res = await fetch(`/api/merchants/${mId}`);
    if (!res.ok) {
      document.getElementById('merchantName').innerText = 'Merchant Not Found';
      return;
    }

    const data = await res.json();

    // Populate Header & Info
    document.getElementById('merchantName').innerText = data.merchant_name;
    document.getElementById('merchantMeta').innerText = `Merchant ID: ${data.merchant_id} • Category: ${data.merchant_category} • City: ${data.city}, ${data.state} • Onboarded: ${data.onboarding_date}`;

    // Populate Decision Banner
    document.getElementById('segmentBadgeContainer').innerHTML = getSegmentBadgeHtml(data.segment);
    document.getElementById('decisionActionTag').innerText = `Recommended Action: ${data.recommended_action}`;
    document.getElementById('decisionExplanation').innerText = data.decision_explanation;

    // Populate Key Metrics
    document.getElementById('detailHealthScore').innerText = data.health_score;
    
    const growthElem = document.getElementById('detailGrowthRate');
    growthElem.innerText = `${data.growth_rate > 0 ? '+' : ''}${data.growth_rate}%`;
    growthElem.style.color = data.growth_rate >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';

    document.getElementById('detailTotalGMV').innerText = formatCurrency(data.total_transaction_value);
    document.getElementById('detailTotalTxns').innerText = formatNumber(data.total_transactions);
    document.getElementById('detailSuccessRate').innerText = `${data.success_rate}%`;
    document.getElementById('detailActiveDays').innerText = `${data.active_days} days`;

    // Populate Health Score Components
    const hc = data.health_components;
    
    document.getElementById('scoreGrowth').innerText = `${hc.growth_score} / 100`;
    document.getElementById('barGrowth').style.width = `${hc.growth_score}%`;

    document.getElementById('scoreFrequency').innerText = `${hc.frequency_score} / 100`;
    document.getElementById('barFrequency').style.width = `${hc.frequency_score}%`;

    document.getElementById('scoreRecency').innerText = `${hc.recency_score} / 100`;
    document.getElementById('barRecency').style.width = `${hc.recency_score}%`;

    document.getElementById('scoreValue').innerText = `${hc.value_score} / 100`;
    document.getElementById('barValue').style.width = `${hc.value_score}%`;

    document.getElementById('scoreSuccess').innerText = `${hc.success_rate_score} / 100`;
    document.getElementById('barSuccess').style.width = `${hc.success_rate_score}%`;

    // Render 12-Month History Chart
    renderHistoryChart(data.monthly_history);

  } catch (err) {
    console.error('Error loading merchant profile:', err);
  }
}

function renderHistoryChart(history) {
  const labels = history.map(h => h.month);
  const gmvData = history.map(h => h.gmv);
  const volumeData = history.map(h => h.transaction_count);

  const ctx = document.getElementById('chartDetailHistory').getContext('2d');
  if (chartDetailHistory) chartDetailHistory.destroy();

  chartDetailHistory = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Monthly GMV (₹)',
          data: gmvData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.3,
          yAxisID: 'y'
        },
        {
          label: 'Transaction Count',
          data: volumeData,
          borderColor: '#10b981',
          borderWidth: 2,
          borderDash: [4, 4],
          pointRadius: 4,
          tension: 0.3,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#f3f4f6' } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              if (ctx.dataset.yAxisID === 'y') return 'GMV: ' + formatCurrency(ctx.raw);
              return 'Volume: ' + formatNumber(ctx.raw) + ' txns';
            }
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#9ca3af',
            callback: (val) => formatCurrency(val)
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { color: '#10b981' }
        }
      }
    }
  });
}
