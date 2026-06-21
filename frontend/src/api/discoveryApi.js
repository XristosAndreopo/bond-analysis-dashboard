/**
 * API functions for the Watchlist Discovery Engine.
 *
 * This file contains all frontend requests related to discovered bond
 * candidates, provider status, CSV uploads, and discovery actions.
 */

import apiClient from "./apiClient";

/**
 * Fetch provider status/configuration report.
 *
 * @returns {Promise<object>} Provider status report.
 */
export async function fetchDiscoveryProviderStatus() {
  const response = await apiClient.get("/discover-bonds/provider-status/");

  return response.data;
}

/**
 * Fetch visible discovered bond candidates for the authenticated user.
 *
 * Optional params:
 * - discovery_run_id: limits results to one DiscoveryRun.
 *
 * @param {object} params - Optional query parameters.
 * @returns {Promise<Array>} Visible bond candidates.
 */
export async function fetchDiscoveredBonds(params = {}) {
  const response = await apiClient.get("/discover-bonds/", {
    params,
  });

  return response.data;
}

/**
 * Run the backend bond discovery engine.
 *
 * Supported sources:
 * - static_provider
 * - csv_provider
 * - external_json_provider
 *
 * @param {object} payload - Optional discovery filters.
 * @returns {Promise<object>} Discovery run result and visible candidates.
 */
export async function runBondDiscovery(payload = {}) {
  const response = await apiClient.post("/discover-bonds/run/", payload);

  return response.data;
}

/**
 * Clear currently visible discovery results.
 *
 * This marks visible candidates as IGNORED.
 * It does not delete records and does not affect Watchlist or Portfolio items.
 *
 * @param {number|string|null} discoveryRunId - Optional DiscoveryRun id.
 * @returns {Promise<object>} Clear result.
 */
export async function clearCurrentDiscoveryResults(discoveryRunId = null) {
  const payload = discoveryRunId
    ? { discovery_run_id: discoveryRunId }
    : {};

  const response = await apiClient.post(
    "/discover-bonds/clear-current/",
    payload
  );

  return response.data;
}

/**
 * Add a discovered candidate to the user's Watchlist.
 *
 * @param {number|string} candidateId - BondCandidate id.
 * @returns {Promise<object>} Add-to-watchlist result.
 */
export async function addDiscoveredBondToWatchlist(candidateId) {
  const response = await apiClient.post(
    `/discover-bonds/${candidateId}/add-to-watchlist/`
  );

  return response.data;
}

/**
 * Ignore a discovered candidate.
 *
 * @param {number|string} candidateId - BondCandidate id.
 * @returns {Promise<object>} Ignore result.
 */
export async function ignoreDiscoveredBond(candidateId) {
  const response = await apiClient.post(
    `/discover-bonds/${candidateId}/ignore/`
  );

  return response.data;
}

/**
 * Upload a CSV bond universe file.
 *
 * @param {File} file - CSV file selected by the user.
 * @returns {Promise<object>} Upload summary.
 */
export async function uploadDiscoveryCsv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post(
    "/discover-bonds/upload-csv/",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}