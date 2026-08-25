// Merchant Directory Controller

document.addEventListener('DOMContentLoaded', () => {
  loadDirectory();

  document.getElementById('directorySearch').addEventListener('keyup', loadDirectory);
  document.getElementById('directorySegment').addEventListener('change', loadDirectory);
  document.getElementById('directoryCategory').addEventListener('change', loadDirectory);
});

function formatCurrency(amt) {
  if (amt >= 10000000) return '₹' + (amt / 10000000).toFixed(2) + ' Cr';
  if (amt >= 100000) return '₹' + (amt / 100000).toFixed(2) + ' L';
  return '₹' + amt.toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function getSegmentBadgeHtml(segment) {
  switch (segment) {
    case 'High Growth': return `<span class="badge badge-high-growth">🚀 High Growth</span>`;
    case 'Healthy': return `<span class="badge badge-healthy">🟢 Healthy</span>`;
    case 'Stable': return `<span class="badge badge-stable">🔵 Stable</span>`;
    case 'Declining': return `<span class="badge badge-declining">🟡 Declining</span>`;
    case 'At Risk': return `<span class="badge badge-at-risk">🔴 At Risk</span>`;
    default: return `<span class="badge badge-stable">${segment}</span>`;
  }
}

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

async function loadDirectory() {
  const search = document.getElementById('directorySearch').value.trim();
  const segment = document.getElementById('directorySegment').value;
  const category = document.getElementById('directoryCategory').value;

  const tbody = document.getElementById('directoryTableBody');
  if (tbody && tbody.children.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:var(--text-muted); padding:24px;">⚡ Loading merchant index...</td></tr>`;
  }

  let url = `/api/merchants?limit=100&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;
  if (segment) url += `segment=${encodeURIComponent(segment)}&`;
  if (category) url += `category=${encodeURIComponent(category)}&`;

  try {
    const res = await fetch(url);
    const merchants = await res.json();

    document.getElementById('directoryCountSub').innerText = `Showing ${merchants.length} matching merchants`;
    updateLastUpdatedBadge(getFormattedTimestamp(), true);

    tbody.innerHTML = '';

    if (merchants.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:var(--text-muted); padding:24px;">No merchants found.</td></tr>`;
      return;
    }

    merchants.forEach(m => {
      const tr = document.createElement('tr');
      tr.addEventListener('click', () => {
        window.location.href = `/merchants/${m.merchant_id}`;
      });

      const growthClass = m.growth_rate >= 0 ? 'color: var(--accent-green);' : 'color: var(--accent-red);';

      tr.innerHTML = `
        <td class="col-id">${m.merchant_id}</td>
        <td class="col-name" title="${m.merchant_name}">${m.merchant_name}</td>
        <td class="col-cat">${m.merchant_category}</td>
        <td class="col-city">${m.city}</td>
        <td class="col-date">${m.onboarding_date}</td>
        <td class="col-gmv">${formatCurrency(m.total_transaction_value)}</td>
        <td class="col-health">
          <span class="health-score-pill ${m.health_score >= 75 ? 'health-high' : m.health_score >= 50 ? 'health-mid' : 'health-low'}">
            ${m.health_score}
          </span>
        </td>
        <td class="col-growth" style="${growthClass}">${m.growth_rate > 0 ? '+' : ''}${m.growth_rate}%</td>
        <td class="col-success">${m.success_rate}%</td>
        <td class="col-segment">${getSegmentBadgeHtml(m.segment)}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Error loading merchant directory:', err);
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

