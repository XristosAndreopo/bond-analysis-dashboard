/**
 * Authentication storage service.
 *
 * This module centralizes how JWT tokens and the logged-in user are stored
 * in browser localStorage.
 *
 * It also keeps backward-compatible helper functions so older components
 * can still work if they import names such as:
 * - saveTokens
 * - storeTokens
 * - clearTokens
 * - getAccessToken
 * - getStoredUser
 */

const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const USER_KEY = "bondAnalysisUser";

/**
 * Extra key names are checked for compatibility with earlier code versions.
 * This helps avoid breaking the app if older files used a different localStorage
 * key name.
 */
const ACCESS_TOKEN_FALLBACK_KEYS = ["access_token", "access"];
const REFRESH_TOKEN_FALLBACK_KEYS = ["refresh_token", "refresh"];
const USER_FALLBACK_KEYS = ["currentUser", "user", "authUser"];

/**
 * Store JWT tokens in localStorage.
 *
 * @param {object|string} accessOrTokenObject - Access token or token object.
 * @param {string} refreshToken - Refresh token.
 */
export function storeTokens(accessOrTokenObject, refreshToken = "") {
  if (typeof accessOrTokenObject === "object" && accessOrTokenObject !== null) {
    const access = accessOrTokenObject.access || accessOrTokenObject.accessToken;
    const refresh =
      accessOrTokenObject.refresh || accessOrTokenObject.refreshToken;

    if (access) {
      localStorage.setItem(ACCESS_TOKEN_KEY, access);
    }

    if (refresh) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    }

    return;
  }

  if (accessOrTokenObject) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessOrTokenObject);
  }

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Alias for storeTokens.
 *
 * Some pages may already use saveTokens, so we keep it for compatibility.
 *
 * @param {object|string} accessOrTokenObject - Access token or token object.
 * @param {string} refreshToken - Refresh token.
 */
export function saveTokens(accessOrTokenObject, refreshToken = "") {
  storeTokens(accessOrTokenObject, refreshToken);
}

/**
 * Get the stored access token.
 *
 * @returns {string|null} Access token.
 */
export function getAccessToken() {
  const primaryToken = localStorage.getItem(ACCESS_TOKEN_KEY);

  if (primaryToken) {
    return primaryToken;
  }

  for (const key of ACCESS_TOKEN_FALLBACK_KEYS) {
    const token = localStorage.getItem(key);

    if (token) {
      return token;
    }
  }

  return null;
}

/**
 * Get the stored refresh token.
 *
 * @returns {string|null} Refresh token.
 */
export function getRefreshToken() {
  const primaryToken = localStorage.getItem(REFRESH_TOKEN_KEY);

  if (primaryToken) {
    return primaryToken;
  }

  for (const key of REFRESH_TOKEN_FALLBACK_KEYS) {
    const token = localStorage.getItem(key);

    if (token) {
      return token;
    }
  }

  return null;
}

/**
 * Store the authenticated user in localStorage.
 *
 * @param {object} user - Current authenticated user.
 */
export function setStoredUser(user) {
  if (!user) {
    return;
  }

  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Alias for setStoredUser.
 *
 * @param {object} user - Current authenticated user.
 */
export function storeUser(user) {
  setStoredUser(user);
}

/**
 * Alias for setStoredUser.
 *
 * @param {object} user - Current authenticated user.
 */
export function saveUser(user) {
  setStoredUser(user);
}

/**
 * Get the authenticated user from localStorage.
 *
 * @returns {object|null} Stored user object.
 */
export function getStoredUser() {
  const primaryUser = parseStoredUser(localStorage.getItem(USER_KEY));

  if (primaryUser) {
    return primaryUser;
  }

  for (const key of USER_FALLBACK_KEYS) {
    const fallbackUser = parseStoredUser(localStorage.getItem(key));

    if (fallbackUser) {
      return fallbackUser;
    }
  }

  return null;
}

/**
 * Parse a JSON user safely.
 *
 * @param {string|null} value - Raw localStorage value.
 * @returns {object|null} Parsed user or null.
 */
function parseStoredUser(value) {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch (error) {
    return null;
  }
}

/**
 * Check if the user appears authenticated.
 *
 * @returns {boolean} True when an access token exists.
 */
export function isAuthenticated() {
  return Boolean(getAccessToken());
}

/**
 * Clear JWT tokens and stored user data.
 */
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);

  ACCESS_TOKEN_FALLBACK_KEYS.forEach((key) => {
    localStorage.removeItem(key);
  });

  REFRESH_TOKEN_FALLBACK_KEYS.forEach((key) => {
    localStorage.removeItem(key);
  });

  USER_FALLBACK_KEYS.forEach((key) => {
    localStorage.removeItem(key);
  });
}

/**
 * Alias for clearTokens.
 */
export function logout() {
  clearTokens();
}

export default {
  storeTokens,
  saveTokens,
  getAccessToken,
  getRefreshToken,
  setStoredUser,
  storeUser,
  saveUser,
  getStoredUser,
  isAuthenticated,
  clearTokens,
  logout,
};