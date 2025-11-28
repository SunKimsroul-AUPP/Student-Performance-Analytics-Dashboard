// Use the same token key as login.js
const AUTH_TOKEN_KEY = "access_token";

function getAccessToken() {
  // Prefer the newer `access_token`, fall back to legacy `spa_token` for older logins
  return (
    localStorage.getItem(AUTH_TOKEN_KEY) ||
    localStorage.getItem("spa_token") ||
    ""
  );
}

// Shared Authorization header
function getAuthHeaders(extra = {}) {
  const token = getAccessToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra };
}

async function fetchJSONAuth(url, options = {}) {
  const headers = { ...(options.headers || {}), ...getAuthHeaders() };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    // Try to get response body for better error messages
    let body = "";
    try {
      body = await res.text();
    } catch (e) {
      body = "(unable to read response body)";
    }
    const msg = `Failed: ${url} (${res.status}) ${body}`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return res.json();
}

// Get current user info from backend
async function fetchCurrentUser() {
  try {
    return await fetchJSONAuth("/api/auth/me");
  } catch {
    return null;
  }
}

// Ensure the navbar logout/login button works even if other scripts haven't wired it.
function initNavbarLogoutFallback() {
  const btn = document.getElementById("logout-btn");
  if (!btn) return;

  // Set label according to current auth state
  const token = getAccessToken();
  btn.textContent = token ? "Logout" : "Login";

  // Add a safe click handler (uses addEventListener to avoid overwriting other handlers)
  const handler = e => {
    e.preventDefault();
    if (getAccessToken()) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem("spa_token");
      localStorage.removeItem("spa_role");
      localStorage.removeItem("spa_username");
      sessionStorage.removeItem("spa_cached_role");
      sessionStorage.removeItem("spa_cached_username");
      window.location.href = "/login.html";
    } else {
      window.location.href = "/login.html";
    }
  };

  // Avoid adding the same handler multiple times by tagging the element
  if (!btn.__navbarAuthFallbackInstalled) {
    btn.addEventListener("click", handler);
    btn.__navbarAuthFallbackInstalled = true;
  }
}

// Run fallback wiring immediately so pages that load `auth.js` early get a working button
try {
  if (typeof window !== "undefined") {
    // Defer slightly to give DOM a moment to parse on some pages
    window.addEventListener("DOMContentLoaded", initNavbarLogoutFallback);
  }
} catch (e) {
  // ignore
}

// Prefer spa_* (set by login.js), fall back to cached values
function getCurrentRole() {
  const direct = localStorage.getItem("spa_role");
  if (direct) return direct;
  const cached = sessionStorage.getItem("spa_cached_role");
  return cached || null;
}

function getCurrentUsername() {
  const direct = localStorage.getItem("spa_username");
  if (direct) return direct;
  const cached = sessionStorage.getItem("spa_cached_username");
  return cached || null;
}

// Redirect to login if not logged in
function requireLogin() {
  const token = getAccessToken();
  if (!token) {
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

// Update login/logout link and role label on "old" navbar
async function setupLoginLink() {
  const link = document.getElementById("login-link");
  const roleSpan = document.getElementById("role-indicator");

  const token = getAccessToken();
  if (!token) {
    if (roleSpan) roleSpan.textContent = "Not logged in";
    if (link) {
      link.textContent = "Login";
      link.href = "/login.html";
      link.onclick = null;
    }
    // clear cached role
    sessionStorage.removeItem("spa_cached_role");
    sessionStorage.removeItem("spa_cached_username");
    return;
  }

  // Try to reuse stored values first
  let role = getCurrentRole();
  let username = getCurrentUsername();

  // Optionally refresh from backend once per session
  if (!role || !username) {
    const user = await fetchCurrentUser();
    if (user) {
      role = user.role || role || "";
      username = user.username || username || "";
      if (role) sessionStorage.setItem("spa_cached_role", role);
      if (username) sessionStorage.setItem("spa_cached_username", username);
    }
  }

  if (roleSpan) {
    roleSpan.textContent = role
      ? `Logged in as ${role}${username ? " (" + username + ")" : ""}`
      : `Logged in as ${username || "user"}`;
  }

  if (link) {
    link.textContent = "Logout";
    link.href = "#";
    link.onclick = e => {
      e.preventDefault();
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem("spa_token");
      localStorage.removeItem("spa_role");
      localStorage.removeItem("spa_username");
      sessionStorage.removeItem("spa_cached_role");
      sessionStorage.removeItem("spa_cached_username");
      window.location.href = "/login.html";
    };
  }
}