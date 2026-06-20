/**
 * API functions for bond master data and market data.
 *
 * These functions allow the frontend to:
 * - search existing bonds
 * - create new bond records
 * - create or update manual market data
 */

import apiClient from "./apiClient";

/**
 * Fetch bonds from the backend.
 *
 * @param {string} searchTerm - Optional search term for ISIN, name, or issuer.
 * @returns {Promise<Array>} List of bonds.
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
 * @param {object} payload - Bond form data.
 * @returns {Promise<object>} Created bond.
 */
export async function createBond(payload) {
  const response = await apiClient.post("/bonds/", payload);

  return response.data;
}

/**
 * Create or update manual market data for a bond.
 *
 * The backend behaves like an upsert for the same:
 * - bond
 * - quote_date
 * - source
 *
 * @param {object} payload - Market data form data.
 * @returns {Promise<object>} Created or updated market data.
 */
export async function createMarketData(payload) {
  const response = await apiClient.post("/market-data/", payload);

  return response.data;
}