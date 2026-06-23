/**
 * Authentication API functions.
 *
 * This file contains all requests related to:
 * - login
 * - signup
 * - email verification
 * - forgot password
 * - password reset
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
 * Register a new inactive user account.
 *
 * The backend sends an email verification code after successful signup.
 *
 * @param {object} payload - Signup form data.
 * @returns {Promise<object>} Created account response.
 */
export async function signupUser(payload) {
  const response = await apiClient.post("/accounts/signup/", payload);

  return response.data;
}

/**
 * Verify an email address with a temporary numeric code.
 *
 * @param {string} email - User email.
 * @param {string} code - Temporary verification code.
 * @returns {Promise<object>} Verification response.
 */
export async function verifyEmail(email, code) {
  const response = await apiClient.post("/accounts/verify-email/", {
    email,
    code,
  });

  return response.data;
}

/**
 * Resend an email verification code.
 *
 * @param {string} email - User email.
 * @returns {Promise<object>} Generic resend response.
 */
export async function resendVerificationCode(email) {
  const response = await apiClient.post(
    "/accounts/resend-verification-code/",
    {
      email,
    }
  );

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
 * Reset a user's password with a temporary numeric code.
 *
 * @param {object} payload - Reset password payload.
 * @returns {Promise<object>} Reset password response.
 */
export async function resetPassword(payload) {
  const response = await apiClient.post("/accounts/reset-password/", payload);

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
