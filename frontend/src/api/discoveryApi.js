/**
 * API functions for the Watchlist Discovery Engine.
 *
 * This file contains all frontend requests related to discovered bond
 * candidates, provider status, CSV uploads, AI research JSON imports, and
 * discovery actions.
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
 * Import AI-researched discovery JSON.
 *
 * This endpoint does not call OpenAI from the frontend. It sends already
 * structured JSON to the backend import endpoint.
 *
 * The backend validates the payload and creates/updates BondCandidate records
 * with data_origin = AI_RESEARCH.
 *
 * @param {object} payload - DiscoveryResearchResult JSON.
 * @returns {Promise<object>} Import summary.
 */
export async function importAIResearchDiscoveryJson(payload) {
  const response = await apiClient.post(
    "/ai-research/import-discovery/",
    payload
  );

  return response.data;
}

/**
 * Import AI-researched market refresh JSON.
 *
 * This endpoint sends already structured market refresh JSON to the backend.
 * The backend validates the payload and creates/updates BondMarketData records
 * for bonds that already exist in the application.
 *
 * @param {object} payload - BondMarketResearchResult JSON.
 * @returns {Promise<object>} Import summary.
 */
export async function importAIResearchMarketJson(payload) {
  const response = await apiClient.post(
    "/ai-research/import-market/",
    payload
  );

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

/**
 * Test the external JSON/API provider without saving candidates.
 *
 * @returns {Promise<object>} External provider test report.
 */
export async function testExternalDiscoveryProvider() {
  const response = await apiClient.get(
    "/discover-bonds/test-external-provider/"
  );

  return response.data;
}