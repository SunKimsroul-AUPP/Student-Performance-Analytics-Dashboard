// --- token helpers for new code (index/app.js, data.js, etc.) ---
const TOKEN_KEY = "access_token";

function getAccessToken() {
  // Prefer the newer `access_token`, fall back to legacy `spa_token` for older logins
  return localStorage.getItem(TOKEN_KEY) || localStorage.getItem("spa_token") || "";
}

function setAccessToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    // keep legacy key in sync for older pages
    localStorage.setItem("spa_token", token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("spa_token");
  }
}

// Used by data.js and app.js
function getAuthHeaders(extra = {}) {
  const token = getAccessToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra };
}

// --- Login page logic for login.html ---
async function handleLogin() {
  const usernameInput = document.getElementById("login-username");
  const passwordInput = document.getElementById("login-password");
  const msgEl = document.getElementById("login-message");

  const username = usernameInput.value.trim();
  const password = passwordInput.value;

  msgEl.textContent = "";

  if (!username || !password) {
    msgEl.textContent = "Please enter both username and password.";
    return;
  }

  try {
    const body = new URLSearchParams();
    body.set("username", username);
    body.set("password", password);

    const res = await fetch("/api/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(text || `Login failed (${res.status})`);
    }

    const data = await res.json(); // { access_token, token_type, role }
    // New token storage used by dashboards:
    setAccessToken(data.access_token);

    // Also store role/username for auth.js pages
    localStorage.setItem("spa_token", data.access_token);
    localStorage.setItem("spa_role", data.role || "");
    localStorage.setItem("spa_username", username);

    msgEl.classList.remove("text-danger");
    msgEl.classList.add("text-success");
    msgEl.textContent = "Login successful. Redirecting...";

    setTimeout(() => {
      window.location.href = "/";
    }, 600);
  } catch (err) {
    console.error(err);
    msgEl.classList.remove("text-success");
    msgEl.classList.add("text-danger");
    msgEl.textContent = "Login failed. Check username/password.";

    // clear both new and old storage
    setAccessToken("");
    localStorage.removeItem("spa_token");
    localStorage.removeItem("spa_role");
    localStorage.removeItem("spa_username");
  }
}

function initLoginPage() {
  const loginBtn = document.getElementById("login-button");
  if (loginBtn) {
    loginBtn.addEventListener("click", handleLogin);
  }

  const pwdEl = document.getElementById("login-password");
  if (pwdEl) {
    pwdEl.addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleLogin();
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Only does anything on login.html
  initLoginPage();
});

/**
 * Shared navbar auth for pages that use:
 *   <span id="nav-user"></span>
 *   <button id="logout-btn">Logout</button>
 *
 * This is the same behavior you had in app.js for the Overview.
 */
function initNavbarAuthShared() {
  const logoutBtn = document.getElementById("logout-btn");
  const navUser = document.getElementById("nav-user");

  const token = getAccessToken();

  if (navUser) {
    if (!token) {
      navUser.textContent = "";
    } else {
      fetch("/api/auth/me", { headers: getAuthHeaders() })
        .then(res => (res.ok ? res.json() : null))
        .then(user => {
          if (user) {
            const role = user.role || "";
            navUser.textContent = role
              ? `Logged in as ${user.username} (${role})`
              : `Logged in as ${user.username}`;
          }
        })
        .catch(() => {
          // Don't overwrite any existing fallback values from localStorage/sessionStorage.
          // If no stored values exist, clear the nav text.
          const storedRole = localStorage.getItem('spa_role') || sessionStorage.getItem('spa_cached_role');
          const storedUser = localStorage.getItem('spa_username') || sessionStorage.getItem('spa_cached_username');
          if (!storedRole && !storedUser) {
            navUser.textContent = "";
          }
        });
    }
  }

  if (logoutBtn) {
    // Clear any previously attached handlers and set behavior based on auth
    logoutBtn.onclick = null;

    if (!token) {
      // If not logged in, show "Login" and send user to login page
      logoutBtn.textContent = "Login";
      logoutBtn.onclick = () => {
        window.location.href = "/login.html";
      };
    } else {
      // Logged in -> show Logout and clear tokens on click
      logoutBtn.textContent = "Logout";
      logoutBtn.onclick = () => {
        setAccessToken("");
        localStorage.removeItem("spa_token");
        localStorage.removeItem("spa_role");
        localStorage.removeItem("spa_username");
        sessionStorage.removeItem("spa_cached_role");
        sessionStorage.removeItem("spa_cached_username");
        window.location.href = "/login.html";
      };
    }
  }
}