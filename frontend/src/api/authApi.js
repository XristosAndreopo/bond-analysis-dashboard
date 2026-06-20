/**
 * Authentication API functions.
 *
 * This file contains all requests related to login and current user retrieval.
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
 * Return the currently authenticated user.
 *
 * @returns {Promise<object>} Current user data.
 */
export async function getCurrentUser() {
  const response = await apiClient.get("/accounts/me/");

  return response.data;
}