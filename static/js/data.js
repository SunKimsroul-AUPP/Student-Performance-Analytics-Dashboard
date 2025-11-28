async function fetchJSONAuth(url, options = {}) {
  const headers = { ...(options.headers || {}), ...getAuthHeaders() };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) throw new Error(`Failed: ${url} (${res.status})`);
  return res.json();
}

async function loadStatus() {
  const data = await fetchJSONAuth("/api/admin/data-status");
  const pre = document.getElementById("data-status");
  pre.textContent = JSON.stringify(data, null, 2);
}

async function uploadCSV(tableName, inputId) {
  const input = document.getElementById(inputId);
  const file = input.files[0];
  const msg = document.getElementById("upload-message");

  if (!file) {
    msg.textContent = `Please select a CSV file for ${tableName}.`;
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`/api/admin/upload/${tableName}`, {
      method: "POST",
      body: formData,
      headers: getAuthHeaders(),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.detail || JSON.stringify(json));
    }
    msg.textContent = json.message || `Uploaded ${tableName} successfully.`;
    await loadStatus();
  } catch (err) {
    console.error(err);
    msg.textContent = `Error uploading ${tableName}: ${err.message}`;
  }
}

/* Adjusted init: loadStatus + initDownloadButtons */
(async function init() {
  try {
    await loadStatus();
  } catch (err) {
    console.error(err);
    document.getElementById("data-status").textContent =
      "Failed to load data status. You might not be logged in as admin.";
  }
})();