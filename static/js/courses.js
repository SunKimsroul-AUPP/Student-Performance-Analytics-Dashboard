async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed: ${url} (${res.status})`);
  return res.json();
}

async function loadPassRates() {
  const data = await fetchJSON("/api/metrics/pass-rates");
  const labels = data.map(d => d.course_id);
  const values = data.map(d => d.pass_rate);
  const ctx = document.getElementById("passChart").getContext("2d");

  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Pass Rate",
        data: values,
        backgroundColor: "#4e79a7",
      }]
    },
    options: {
      scales: {
        y: { min: 0, max: 1, title: { display: true, text: "Pass Rate" } }
      }
    }
  });
}

async function loadDFWRates() {
  const data = await fetchJSON("/api/metrics/dfw-rates");
  const labels = data.map(d => d.course_id);
  const values = data.map(d => d.dfw_rate);
  const ctx = document.getElementById("dfwChart").getContext("2d");

  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "DFW Rate",
        data: values,
        backgroundColor: "#e15759",
      }]
    },
    options: {
      scales: {
        y: { min: 0, max: 1, title: { display: true, text: "DFW Rate" } }
      }
    }
  });
}

async function loadCourseTable() {
  const passData = await fetchJSON("/api/metrics/pass-rates");
  const dfwData = await fetchJSON("/api/metrics/dfw-rates");
  const dfwIndex = new Map(dfwData.map(d => [d.course_id, d.dfw_rate]));

  const tbody = document.querySelector("#course-table tbody");
  tbody.innerHTML = "";

  passData.forEach(row => {
    const dfwRate = dfwIndex.get(row.course_id) ?? 0;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.course_id}</td>
      <td>${row.title}</td>
      <td>${row.department || ""}</td>
      <td>${row.level || ""}</td>
      <td>${(row.pass_rate * 100).toFixed(1)}%</td>
      <td>${(dfwRate * 100).toFixed(1)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

(async function init() {
  try {
    await Promise.all([
      loadPassRates(),
      loadDFWRates(),
      loadCourseTable(),
    ]);
  } catch (err) {
    console.error(err);
    alert("Failed to load course analytics. Check backend.");
  }
})();