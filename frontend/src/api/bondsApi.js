/**
 * API functions for bond master data, market data, and FX rates.
 *
 * These functions allow the frontend to:
 * - search existing bonds
 * - create new bond records
 * - create or update manual market data
 * - fetch stored FX rates
 * - trigger live FX rate updates
 */

import apiClient from "./apiClient";

/**
 * Fetch bond master data.
 *
 * @param {string} searchTerm - Optional search term.
 * @returns {Promise<Array>} Bond records.
 */
export async function fetchBonds(searchTerm = "") {
  const response = await apiClient.get("/bonds/", {
    params: {
      search: searchTerm,
    },
  });

  return response.data;
}

/**
 * Create a new bond.
 *
 * @param {object} payload - Bond data.
 * @returns {Promise<object>} Created bond.
 */
export async function createBond(payload) {
  const response = await apiClient.post("/bonds/", payload);

  return response.data;
}

/**
 * Create or update market data for a bond.
 *
 * @param {object} payload - Market data payload.
 * @returns {Promise<object>} Saved market data.
 */
export async function createMarketData(payload) {
  const response = await apiClient.post("/market-data/", payload);

  return response.data;
}

/**
 * Fetch stored FX rates.
 *
 * @param {object} params - Optional query params, e.g. quote_currency.
 * @returns {Promise<Array|object>} FX rate response.
 */
export async function fetchFXRates(params = {}) {
  const response = await apiClient.get("/fx-rates/", {
    params,
  });

  return response.data;
}

/**
 * Trigger live FX rate update from backend.
 *
 * @param {object} payload - Update payload.
 * @returns {Promise<object>} Update result.
 */
export async function updateFXRates(payload) {
  const response = await apiClient.post("/fx-rates/update/", payload);

  return response.data;
}