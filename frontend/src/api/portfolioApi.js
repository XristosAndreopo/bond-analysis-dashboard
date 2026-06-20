/**
 * API functions for Dashboard, Portfolio, Watchlist, and bond detail pages.
 *
 * All functions use the central Axios API client, which automatically attaches
 * the JWT access token when it exists.
 */

import apiClient from "./apiClient";

/**
 * Fetch dashboard data for the authenticated user.
 *
 * @returns {Promise<object>} Dashboard data.
 */
export async function fetchDashboard() {
  const response = await apiClient.get("/dashboard/");

  return response.data;
}

/**
 * Fetch portfolio data for the authenticated user.
 *
 * @returns {Promise<object>} Portfolio data.
 */
export async function fetchPortfolio() {
  const response = await apiClient.get("/portfolio/");

  return response.data;
}

/**
 * Fetch watchlist data for the authenticated user.
 *
 * @returns {Promise<object>} Watchlist data.
 */
export async function fetchWatchlist() {
  const response = await apiClient.get("/watchlist/");

  return response.data;
}

/**
 * Fetch one user bond detail.
 *
 * @param {number|string} positionId - UserBond id.
 * @returns {Promise<object>} Position detail data.
 */
export async function fetchPositionDetail(positionId) {
  const response = await apiClient.get(`/positions/${positionId}/`);

  return response.data;
}

/**
 * Create a Portfolio item for the authenticated user.
 *
 * @param {object} payload - UserBond form data.
 * @returns {Promise<object>} Created Portfolio item.
 */
export async function createPortfolioItem(payload) {
  const response = await apiClient.post("/portfolio/", payload);

  return response.data;
}

/**
 * Create a Watchlist item for the authenticated user.
 *
 * @param {object} payload - UserBond form data.
 * @returns {Promise<object>} Created Watchlist item.
 */
export async function createWatchlistItem(payload) {
  const response = await apiClient.post("/watchlist/", payload);

  return response.data;
}

/**
 * Update a user bond position.
 *
 * @param {number|string} positionId - UserBond id.
 * @param {object} payload - Updated UserBond data.
 * @returns {Promise<object>} Updated position response.
 */
export async function updatePosition(positionId, payload) {
  const response = await apiClient.patch(`/positions/${positionId}/`, payload);

  return response.data;
}

/**
 * Soft-delete a user bond position.
 *
 * @param {number|string} positionId - UserBond id.
 * @returns {Promise<void>}
 */
export async function deletePosition(positionId) {
  await apiClient.delete(`/positions/${positionId}/`);
}

/**
 * Move a position between Portfolio and Watchlist.
 *
 * @param {number|string} positionId - UserBond id.
 * @param {object} payload - Move payload.
 * @returns {Promise<object>} Moved position.
 */
export async function movePosition(positionId, payload) {
  const response = await apiClient.post(
    `/positions/${positionId}/move/`,
    payload
  );

  return response.data;
}