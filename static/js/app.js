function riskLevel(score) {
  if (score == null) return { label: "Unknown", className: "risk-unknown" };
  if (score >= 2.0) return { label: "High", className: "risk-high" };
  if (score >= 1.0) return { label: "Medium", className: "risk-medium" };
  return { label: "Low", className: "risk-low" };
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed: ${url} (${res.status})`);
  return res.json();
}

// Single Chart instance for cohort chart so we can destroy/recreate safely
let cohortChart = null;
async function loadHeadlineMetrics() {
  const [summary, atRisk] = await Promise.all([
    fetchJSON("/api/metrics/student-summary"),
    fetchJSON("/api/risk/at-risk"),
  ]);

  const nStudents = summary.length;
  const avgGpa =
    nStudents > 0
      ? summary.reduce((sum, r) => sum + (r.gpa || 0), 0) / nStudents
      : 0.0;
  const nAtRisk = atRisk.length;

  document.getElementById("kpi-total-students").textContent = nStudents;
  document.getElementById("kpi-avg-gpa").textContent = avgGpa.toFixed(2);
  document.getElementById("kpi-at-risk").textContent = nAtRisk;
}

async function loadGpaLeaderboard() {
  const data = await fetchJSON("/api/metrics/student-summary");
  // Read optional filter value (student id substring)
  const filterInput = document.getElementById('gpa-filter');
  const filterVal = filterInput && filterInput.value ? filterInput.value.trim().toLowerCase() : '';
  const tbody = document.querySelector("#gpa-table tbody");
  tbody.innerHTML = "";

  data.sort((a, b) => (b.gpa || 0) - (a.gpa || 0));

  // Apply student id filter if present
  const rows = filterVal
    ? data.filter(r => (r.student_id || '').toLowerCase().includes(filterVal))
    : data;

  for (const row of rows) {
    const gpa = row.gpa != null ? row.gpa.toFixed(2) : "n/a";
    const totalCredits =
      row.total_credits != null ? row.total_credits.toFixed(1) : "0.0";
    const avgAttendance =
      row.avg_attendance != null ? row.avg_attendance.toFixed(1) : "0.0";
    const dfwCount = row.dfw_count != null ? row.dfw_count : 0;
    const creditsAttempted =
      row.credits_attempted != null
        ? row.credits_attempted.toFixed(1)
        : "0.0";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.student_id || ''}</td>
      <td>${row.name || ''}</td>
      <td>${row.major || ""}</td>
      <td>${row.cohort_year || ""}</td>
      <td>${gpa}</td>
      <td>${totalCredits}</td>
      <td>${avgAttendance}</td>
      <td>${dfwCount}</td>
      <td>${creditsAttempted}</td>
    `;
    tbody.appendChild(tr);
  }

  if (!tbody.children.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="9">No GPA data available.</td>`;
    tbody.appendChild(tr);
  }
}

async function loadRiskList() {
  const risk = await fetchJSON("/api/risk/at-risk");
  risk.sort((a, b) => (b.score || 0) - (a.score || 0));

  const list = document.getElementById("risk-list");
  list.innerHTML = "";

  risk.forEach(r => {
    const { label, className } = riskLevel(r.score);
    const score = r.score != null ? r.score.toFixed(2) : "0.00";

    const li = document.createElement("li");
    li.className = `list-group-item ${className}`;

    li.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="risk-name">${r.name || r.student_id}</span>
        <span class="badge rounded-pill bg-light text-dark badge-risk">
          ${label.toUpperCase()}
        </span>
      </div>
      <div class="risk-meta">
        GPA ${r.gpa.toFixed(2)} · Score ${score} · ${(r.flags || []).join(", ")}
      </div>
    `;
    list.appendChild(li);
  });

  if (!risk.length) {
    const li = document.createElement("li");
    li.className = "list-group-item";
    li.textContent = "No at-risk students currently.";
    list.appendChild(li);
  }
}

async function loadCohortChart() {
  let data;
  try {
    data = await fetchJSON("/api/metrics/cohort-gpa");
  } catch (err) {
    console.error("Failed to load cohort GPA:", err);
    return;
  }

  if (!Array.isArray(data) || !data.length) {
    console.warn("No cohort GPA data to display.");
    return;
  }

  const ctx = document.getElementById("cohortChart");
  if (!ctx) return;

  // Sort by cohort_year to ensure the x-axis is ordered
  data.sort((a, b) => a.cohort_year - b.cohort_year);
  const labels = data.map((d) => String(d.cohort_year));
  const means = data.map((d) => d.mean);
  const medians = data.map((d) => d.median);
  const counts = data.map((d) => d.count || 0);

  // If there are many points, hide point markers to reduce clutter
  const manyPoints = labels.length > 50;
  const pointRadius = manyPoints ? 0 : 3;

  // Dynamically size canvas height based on number of points so dense datasets get more vertical space
  try {
    const canvas = document.getElementById("cohortChart");
    const minHeight = 280;
    const perPoint = 6; // px per point
    const calculated = Math.min(1200, Math.max(minHeight, Math.ceil(labels.length * perPoint) + 120));
    canvas.height = calculated;
    canvas.style.height = calculated + "px";
  } catch (e) {
    // ignore sizing errors
  }

  // Destroy existing chart if present
  if (cohortChart) {
    try {
      cohortChart.destroy();
    } catch (e) {
      console.warn("Failed to destroy previous cohortChart:", e);
    }
    cohortChart = null;
  }

  cohortChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Mean GPA",
          data: means,
          borderColor: "#4e79a7",
          backgroundColor: "rgba(78,121,167,0.12)",
          borderWidth: 2,
          tension: 0.15,
          fill: false,
          pointRadius,
          pointHoverRadius: Math.max(4, pointRadius + 2),
        },
        {
          label: "Median GPA",
          data: medians,
          borderColor: "#e15759",
          backgroundColor: "rgba(225,87,89,0.12)",
          borderWidth: 2,
          tension: 0.15,
          fill: false,
          pointRadius,
          pointHoverRadius: Math.max(4, pointRadius + 2),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            title: (items) => {
              if (!items || !items.length) return "";
              return `Cohort ${items[0].label}`;
            },
            label: (ctx) => {
              const val = ctx.parsed.y;
              const datasetLabel = ctx.dataset.label || "";
              const cohortIndex = ctx.dataIndex;
              const count = counts[cohortIndex] || 0;
              return `${datasetLabel}: ${val != null ? val.toFixed(2) : "n/a"} (n=${count})`;
            },
          },
        },
        // Use built-in decimation for large datasets if available (Chart.js >=3)
        decimation: {
          enabled: manyPoints,
          algorithm: "lttb",
          samples: 200,
        },
      },
      scales: {
        x: {
          ticks: {
            autoSkip: true,
            maxTicksLimit: 20,
            maxRotation: 45,
            minRotation: 0,
          },
          grid: { display: false },
        },
        y: {
          min: 0,
          max: 4,
          ticks: {
            stepSize: 0.25,
          },
        },
      },
      elements: {
        point: {
          hitRadius: 8,
        },
      },
    },
  });

  // No interactive zoom/pan controls — chart size is handled above
}

async function initOverview() {
  try {
    await Promise.all([
      loadHeadlineMetrics(),
      loadGpaLeaderboard(),
      loadRiskList(),
      loadCohortChart(),
    ]);
  } catch (err) {
    console.error("Failed to init overview:", err);
  }
}


// Initialize
initOverview();

// Wire filter input to reload leaderboard as user types (small debounce)
try {
  const filterEl = document.getElementById('gpa-filter');
  if (filterEl) {
    let _deb = null;
    filterEl.addEventListener('input', () => {
      if (_deb) clearTimeout(_deb);
      _deb = setTimeout(() => {
        loadGpaLeaderboard().catch(err => console.error('Failed to reload GPA leaderboard:', err));
      }, 250);
    });
  }
} catch (e) {
  // ignore DOM wiring errors
}