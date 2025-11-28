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

async function loadAtRisk(major, cohortYear) {
  // Enriched student summary
  const summary = await fetchJSON("/api/metrics/student-summary");
  // Risk flags + scores
  const risk = await fetchJSON("/api/risk/at-risk");

  const riskIndex = new Map(risk.map(r => [r.student_id, r]));
  const tbody = document.querySelector("#advisor-risk-table tbody");
  tbody.innerHTML = "";

  const rows = [];

  summary.forEach(row => {
    if (major && row.major !== major) return;
    if (cohortYear && String(row.cohort_year) !== String(cohortYear)) return;

    const r = riskIndex.get(row.student_id);
    if (!r) return; // not at risk

    const gpa = row.gpa != null ? row.gpa.toFixed(2) : "n/a";
    const avgAttendance =
      row.avg_attendance != null ? row.avg_attendance.toFixed(1) : "0.0";
    const dfwCount = row.dfw_count != null ? row.dfw_count : 0;
    const creditsAttempted =
      row.credits_attempted != null
        ? row.credits_attempted.toFixed(1)
        : "0.0";
    const scoreValue = r.score || 0;
    const scoreDisplay = r.score != null ? r.score.toFixed(2) : "0.00";
    const flagsStr = (r.flags || []).join(", ");

    rows.push({
      name: row.name || row.student_id,
      major: row.major || "",
      cohort_year: row.cohort_year || "",
      gpa,
      avgAttendance,
      dfwCount,
      creditsAttempted,
      scoreValue,
      scoreDisplay,
      flagsStr,
    });
  });

  // Sort by descending risk score
  rows.sort((a, b) => b.scoreValue - a.scoreValue);

  rows.forEach(row => {
    const { label, className } = riskLevel(row.scoreValue);
    const tr = document.createElement("tr");
    tr.className = className;
    tr.innerHTML = `
      <td>${row.name}</td>
      <td>${row.major}</td>
      <td>${row.cohort_year}</td>
      <td>${row.gpa}</td>
      <td>${row.avgAttendance}</td>
      <td>${row.dfwCount}</td>
      <td>${row.creditsAttempted}</td>
      <td>${row.scoreDisplay} (${label})</td>
      <td>${row.flagsStr}</td>
    `;
    tbody.appendChild(tr);
  });

  if (!tbody.children.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="9">No at-risk students for selected filters.</td>`;
    tbody.appendChild(tr);
  }
}

function initAdvisorPage() {
  const majorSel = document.getElementById("advisor-major");
  const cohortSel = document.getElementById("advisor-cohort");
  const btn = document.getElementById("advisor-apply");

  btn.addEventListener("click", () => {
    loadAtRisk(majorSel.value, cohortSel.value).catch(err => {
      console.error(err);
      alert("Failed to load advisor view.");
    });
  });

  // initial load
  loadAtRisk("", "").catch(err => {
    console.error(err);
    alert("Failed to load advisor view.");
  });
}

initAdvisorPage();