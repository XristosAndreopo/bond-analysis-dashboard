/**
 * API functions for bond master data, market data, and FX rates.
 *
 * These functions allow the frontend to:
 * - search existing bonds
 * - create new bond records
 * - create or update manual market data
 * - trigger live FX rate updates
 */

import apiClient from "./apiClient";

export async function fetchBonds(searchTerm = "") {
  const response = await apiClient.get("/bonds/", {
    params: {
      search: searchTerm,
    },
  });

  return response.data;
}

export async function createBond(payload) {
  const response = await apiClient.post("/bonds/", payload);

  return response.data;
}

export async function createMarketData(payload) {
  const response = await apiClient.post("/market-data/", payload);

  return response.data;
}

export async function fetchFXRates(params = {}) {
  const response = await apiClient.get("/fx-rates/", {
    params,
  });

  return response.data;
}

export async function updateFXRates(payload) {
  const response = await apiClient.post("/fx-rates/update/", payload);

  return response.data;
}