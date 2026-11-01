/**
 * ============================================================
 *  assets/js/auth.js  —  Authentication Layer (v2.1)
 *
 *  📌 WHAT IS THIS?
 *     Handles all authentication logic on the frontend:
 *     - Storing/retrieving JWT tokens from localStorage
 *     - Login / Register API calls
 *     - Navbar state (show username or Login button)
 *     - Redirect protection for login-required pages
 *
 *  📌 HOW JWT WORKS ON THE FRONTEND:
 *     1. User logs in → backend returns a token
 *     2. We store token in localStorage (persists across tabs)
 *     3. Every API call to protected endpoints includes:
 *        Authorization: Bearer <token>
 *     4. On logout, we remove the token from localStorage
 * ============================================================
 */

const AUTH_TOKEN_KEY = "resumeai_jwt_token";
const AUTH_USER_KEY  = "resumeai_user";


// ─────────────────────────────────────────────
// TOKEN STORAGE HELPERS
// ─────────────────────────────────────────────

/**
 * Save JWT token and user info after login/register.
 * @param {string} token - The JWT token from the server
 * @param {object} user  - The user object { id, username, email, ... }
 */
function saveAuthData(token, user) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

/**
 * Get the stored JWT token.
 * Returns null if not logged in.
 */
function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get the stored user object.
 * Returns null if not logged in.
 */
function getCurrentUser() {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

/**
 * Check if the user is currently logged in.
 */
function isLoggedIn() {
    return !!getToken();
}

/**
 * Log out — remove token and user data, redirect to home.
 */
function logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    window.location.href = resolveIndexPath();
}

/**
 * Get the path to index.html relative to current page.
 * (Works for both root-level and pages/ subdirectory)
 */
function resolveIndexPath() {
    const path = window.location.pathname;
    if (path.includes("/pages/")) {
        return "../index.html";
    }
    return "index.html";
}


// ─────────────────────────────────────────────
// API HELPERS WITH AUTH HEADER
// ─────────────────────────────────────────────

/**
 * Build request headers including JWT token if logged in.
 */
function getAuthHeaders() {
    const token = getToken();
    const headers = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
}


// ─────────────────────────────────────────────
// AUTH API CALLS
// ─────────────────────────────────────────────

/**
 * Register a new user account.
 * @returns {Promise<object>} - { access_token, user }
 */
async function registerUser(username, email, password, fullName = "") {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username,
            email,
            password,
            full_name: fullName
        })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
    }

    // Save auth data
    saveAuthData(data.access_token, data.user);
    return data;
}

/**
 * Log in with email + password.
 * @returns {Promise<object>} - { access_token, user }
 */
async function loginUser(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Login failed");
    }

    // Save auth data
    saveAuthData(data.access_token, data.user);
    return data;
}

/**
 * Verify the current token is still valid.
 * @returns {Promise<object|null>} - User object or null if expired
 */
async function verifyToken() {
    const token = getToken();
    if (!token) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) {
            // Token expired or invalid — clean up
            localStorage.removeItem(AUTH_TOKEN_KEY);
            localStorage.removeItem(AUTH_USER_KEY);
            return null;
        }
        return await response.json();
    } catch {
        return null;
    }
}

/**
 * Fetch the user's scan history.
 * @param {number} limit  - How many to fetch (default 20)
 * @param {number} offset - Pagination offset (default 0)
 */
async function fetchHistory(limit = 20, offset = 0) {
    const token = getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_BASE_URL}/history?limit=${limit}&offset=${offset}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to fetch history");
    }

    return await response.json();
}

/**
 * Fetch the full result of a specific past scan.
 * @param {number} scanId - The scan history ID
 */
async function fetchHistoryDetail(scanId) {
    const token = getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_BASE_URL}/history/${scanId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to fetch scan detail");
    }

    return await response.json();
}

/**
 * Delete a specific history record.
 * @param {number} scanId - The scan history ID
 */
async function deleteHistoryItem(scanId) {
    const token = getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_BASE_URL}/history/${scanId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok && response.status !== 204) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to delete scan");
    }
}

/**
 * Clear all history for the current user.
 */
async function clearAllHistory() {
    const token = getToken();
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_BASE_URL}/history`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok && response.status !== 204) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to clear history");
    }
}


// ─────────────────────────────────────────────
// NAVBAR STATE MANAGEMENT
// Updates the navbar to show username or Login button
// Call this on every page that loads auth.js
// ─────────────────────────────────────────────

function updateNavbarAuthState() {
    const navButtons = document.querySelector(".nav-buttons");
    const historyNavLink = document.getElementById("historyNavLink");
    const user = getCurrentUser();

    // Toggle history link in nav-links (if present on the page)
    if (historyNavLink) {
        historyNavLink.style.display = user ? "inline-flex" : "none";
    }

    if (!navButtons) return;

    // Check if the current page already has a visible/configured history link in nav-links
    const hasHistoryInNav = !!document.querySelector('.nav-links a[href*="history"]');

    if (user) {
        // Only show history button in nav-buttons if nav-links does NOT already have history
        const showHistoryInButtons = !hasHistoryInNav;
        navButtons.innerHTML = `
            ${showHistoryInButtons ? `
            <a href="${resolveHistoryPath()}" class="nav-link-btn" title="View History">
                <i class="fa-solid fa-clock-rotate-left"></i> History
            </a>` : ""}
            <div class="user-badge" title="Logged in as ${user.username}">
                <i class="fa-solid fa-circle-user"></i>
                <span>${user.username}</span>
            </div>
            <button class="secondary-btn small-btn logout-btn" onclick="logout()" title="Logout">
                <i class="fa-solid fa-right-from-bracket"></i> Logout
            </button>
        `;
    } else {
        // Show Login + Register buttons
        navButtons.innerHTML = `
            <a href="${resolveLoginPath()}" class="secondary-btn small-btn">
                <i class="fa-solid fa-right-to-bracket"></i> Login
            </a>
            <a href="${resolveRegisterPath()}" class="primary-btn small-btn">
                Get Started
            </a>
        `;
    }
}

function resolveLoginPath() {
    return window.location.pathname.includes("/pages/") ? "login.html" : "pages/login.html";
}

function resolveRegisterPath() {
    return window.location.pathname.includes("/pages/") ? "register.html" : "pages/register.html";
}

function resolveHistoryPath() {
    return window.location.pathname.includes("/pages/") ? "history.html" : "pages/history.html";
}


// ─────────────────────────────────────────────
// SMART FLOATING NAVBAR (Modern Hide-on-Scroll)
// Slides up and hides when scrolling DOWN
// Reappears smoothly when scrolling UP or at the top
// ─────────────────────────────────────────────

function initSmartNavbar() {
    const navbar = document.querySelector(".navbar");
    if (!navbar) return;

    let lastScrollY = window.pageYOffset || document.documentElement.scrollTop;
    let ticking = false;

    window.addEventListener("scroll", () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const currentScrollY = window.pageYOffset || document.documentElement.scrollTop;

                // Near top -> always visible & clean
                if (currentScrollY <= 15) {
                    navbar.classList.remove("navbar--hidden");
                    navbar.classList.remove("navbar--scrolled");
                } else {
                    navbar.classList.add("navbar--scrolled");

                    // Scroll Down -> Hide navbar
                    if (currentScrollY > lastScrollY + 6 && currentScrollY > 70) {
                        navbar.classList.add("navbar--hidden");
                    }
                    // Scroll Up -> Reveal navbar
                    else if (currentScrollY < lastScrollY - 6) {
                        navbar.classList.remove("navbar--hidden");
                    }
                }

                lastScrollY = currentScrollY <= 0 ? 0 : currentScrollY;
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
}


// ─────────────────────────────────────────────
// REDIRECT PROTECTION
// Call on pages that require authentication
// ─────────────────────────────────────────────

function requireAuth() {
    if (!isLoggedIn()) {
        const loginPath = window.location.pathname.includes("/pages/")
            ? "login.html"
            : "pages/login.html";
        window.location.href = loginPath;
    }
}

// ─────────────────────────────────────────────
// AUTO-INIT: Update navbar on every page load
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    updateNavbarAuthState();
    initSmartNavbar();
});

