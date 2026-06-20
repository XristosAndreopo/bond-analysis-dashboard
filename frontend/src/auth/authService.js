/**
 * Client-side authentication helpers.
 *
 * Tokens are stored in localStorage for this MVP. Later, we may improve this
 * by using httpOnly cookies depending on deployment/security requirements.
 */

const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";

/**
 * Store JWT tokens.
 *
 * @param {object} tokens - JWT token object returned by the backend.
 */
export function storeTokens(tokens) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

/**
 * Remove JWT tokens from localStorage.
 */
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if the user appears authenticated.
 *
 * This only checks token existence. The backend remains the source of truth.
 *
 * @returns {boolean}
 */
export function isAuthenticated() {
  return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));
}