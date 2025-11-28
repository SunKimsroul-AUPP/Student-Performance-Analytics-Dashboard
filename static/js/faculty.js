async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed: ${url} (${res.status})`);
  return res.json();
}

function getSelectedFilters() {
  const deptSel = document.getElementById("faculty-dept");
  const termSel = document.getElementById("faculty-term");
  return {
    department: deptSel ? deptSel.value : "",
    term: termSel ? termSel.value : "",
  };
}

function buildQuery(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      usp.set(k, v);
    }
  });
  const q = usp.toString();
  return q ? `?${q}` : "";
}

async function loadPassAndDFWCharts() {
  const { department, term } = getSelectedFilters();
  const query = buildQuery({ department, term });

  let passRates = [];
  let dfwRates = [];
  try {
    [passRates, dfwRates] = await Promise.all([
      fetchJSON(`/api/metrics/pass-rates${query}`),
      fetchJSON(`/api/metrics/dfw-rates${query}`),
    ]);
  } catch (err) {
    console.error("Error fetching pass/dfw rates:", err);
    // Leave charts blank instead of breaking the page
    return;
  }

  if (!Array.isArray(passRates)) passRates = [];
  if (!Array.isArray(dfwRates)) dfwRates = [];

  const passCtx = document.getElementById("facultyPassChart");
  const dfwCtx = document.getElementById("facultyDFWChart");
  if (!passCtx || !dfwCtx) return;

  // Destroy old charts if they exist
  if (window._facultyPassChart) window._facultyPassChart.destroy();
  if (window._facultyDFWChart) window._facultyDFWChart.destroy();

  if (!passRates.length) {
    // Just initialize empty charts
    window._facultyPassChart = new Chart(passCtx, {
      type: "bar",
      data: { labels: [], datasets: [] },
      options: { responsive: true },
    });
    window._facultyDFWChart = new Chart(dfwCtx, {
      type: "bar",
      data: { labels: [], datasets: [] },
      options: { responsive: true },
    });
    return;
  }

  const labels = passRates.map(r => `${r.course_id} ${r.title || ""}`);
  const passData = passRates.map(r => (r.pass_rate || 0) * 100);

  const dfwMap = new Map(
    dfwRates.map(r => [r.course_id, (r.dfw_rate || 0) * 100])
  );
  const dfwData = passRates.map(r => dfwMap.get(r.course_id) ?? 0);

  window._facultyPassChart = new Chart(passCtx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Pass rate (%)",
          data: passData,
          backgroundColor: "rgba(78, 121, 167, 0.7)",
        },
      ],
    },
    options: {
      responsive: true,
      indexAxis: "y",
      scales: {
        x: {
          min: 0,
          max: 100,
          ticks: { callback: v => `${v}%` },
        },
      },
    },
  });

  window._facultyDFWChart = new Chart(dfwCtx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "DFW rate (%)",
          data: dfwData,
          backgroundColor: "rgba(225, 87, 89, 0.7)",
        },
      ],
    },
    options: {
      responsive: true,
      indexAxis: "y",
      scales: {
        x: {
          min: 0,
          max: 100,
          ticks: { callback: v => `${v}%` },
        },
      },
    },
  });
}

// Gateway UI removed: not rendering per user's request

async function loadAllCoursePrereqs() {
  const container = document.getElementById('all-course-prereqs');
  if (!container) return;
  container.innerHTML = '';

  let full = [];
  try {
    full = await fetchJSON('/api/graph/prerequisites/full');
  } catch (e) {
    console.error('Failed to fetch full prerequisites:', e);
    container.textContent = 'Could not load course prerequisites.';
    return;
  }

  // Sort by course id
  full.sort((a,b) => (a.course_id || '').localeCompare(b.course_id || ''));

  full.forEach(item => {
    const cid = item.course_id;
    const title = item.title || '';
    const pres = item.prerequisites || [];

    const entry = document.createElement('div');
    entry.className = 'list-group-item';

    const header = document.createElement('div');
    header.className = 'd-flex justify-content-between align-items-center';
    header.innerHTML = `<div><strong>${cid}</strong>${title ? ' — ' + title : ''}</div><div class="text-muted small">${pres.length ? pres.length + ' prereq(s)' : 'No prerequisites'}</div>`;
    entry.appendChild(header);

    const body = document.createElement('div');
    body.className = 'mt-2 small';
    if (!pres.length) {
      body.textContent = 'None';
    } else {
      const ul = document.createElement('ul');
      ul.className = 'mb-0 ps-3';
      pres.forEach(p => {
        const pli = document.createElement('li');
        const pid = p.course_id || p[0] || p;
        const ptitle = p.title || p[1] || '';
        pli.textContent = ptitle ? `${pid} — ${ptitle}` : pid;
        ul.appendChild(pli);
      });
      body.appendChild(ul);
    }

    entry.appendChild(body);
    container.appendChild(entry);
  });
}

async function loadFacultyView() {
  await loadPassAndDFWCharts();
  await loadAllCoursePrereqs();
}

function initFacultyPage() {
  const applyBtn = document.getElementById("faculty-apply");
  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      loadFacultyView().catch(err => {
        console.error("Unexpected error in loadFacultyView:", err);
        // No alert; fail silently and log to console
      });
    });
  }

  // Initial load
  loadFacultyView().catch(err => {
    console.error("Unexpected error in initial loadFacultyView:", err);
    // No alert
  });
}

initFacultyPage();