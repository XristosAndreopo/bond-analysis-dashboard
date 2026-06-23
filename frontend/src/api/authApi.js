/**
 * Authentication API functions.
 *
 * This file contains all requests related to:
 * - login
 * - signup
 * - forgot password
 * - current authenticated user retrieval
 */

import apiClient from "./apiClient";

/**
 * Request JWT access and refresh tokens from the backend.
 *
 * @param {string} username - User's username.
 * @param {string} password - User's password.
 * @returns {Promise<object>} JWT token response.
 */
export async function loginUser(username, password) {
  const response = await apiClient.post("/auth/token/", {
    username,
    password,
  });

  return response.data;
}

/**
 * Register a new user account.
 *
 * @param {object} payload - Signup form data.
 * @returns {Promise<object>} Created account response.
 */
export async function signupUser(payload) {
  const response = await apiClient.post("/accounts/signup/", payload);

  return response.data;
}

/**
 * Request password reset instructions.
 *
 * The backend intentionally returns a generic response so it does not reveal
 * whether the submitted email exists.
 *
 * @param {string} email - User email address.
 * @returns {Promise<object>} Forgot password response.
 */
export async function requestPasswordReset(email) {
  const response = await apiClient.post("/accounts/forgot-password/", {
    email,
  });

  return response.data;
}

/**
 * Return the currently authenticated user.
 *
 * @returns {Promise<object>} Current user data.
 */
export async function getCurrentUser() {
  const response = await apiClient.get("/accounts/me/");

  return response.data;
}