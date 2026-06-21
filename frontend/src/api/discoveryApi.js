/**
 * API functions for the Watchlist Discovery Engine.
 *
 * This file contains all frontend requests related to discovered bond
 * candidates and CSV bond universe uploads.
 *
 * The backend remains responsible for:
 * - running discovery
 * - validating provider data
 * - filtering by rating and maturity
 * - excluding existing Watchlist/Portfolio bonds
 * - adding candidates to the user's Watchlist
 * - ignoring candidates
 * - validating and storing uploaded CSV files
 *
 * The frontend only displays results and sends user actions.
 */

import apiClient from "./apiClient";

/**
 * Fetch visible discovered bond candidates for the authenticated user.
 *
 * The backend returns only candidates that:
 * - belong to the logged-in user
 * - have status NEW or REVIEWED
 * - are not already active in Watchlist
 * - are not already active in Portfolio
 * - are not ignored
 * - are not already added to Watchlist
 *
 * @returns {Promise<Array>} Visible bond candidates.
 */
export async function fetchDiscoveredBonds() {
  const response = await apiClient.get("/discover-bonds/");

  return response.data;
}

/**
 * Run the backend bond discovery engine.
 *
 * Supported sources:
 * - static_provider
 * - csv_provider
 *
 * Example payload:
 * {
 *   source: "csv_provider",
 *   min_rating: "BBB-",
 *   currencies: ["EUR"],
 *   countries: ["GR"]
 * }
 *
 * @param {object} payload - Optional discovery filters.
 * @returns {Promise<object>} Discovery run result and visible candidates.
 */
export async function runBondDiscovery(payload = {}) {
  const response = await apiClient.post("/discover-bonds/run/", payload);

  return response.data;
}

/**
 * Add a discovered candidate to the user's Watchlist.
 *
 * The backend will:
 * - create the Bond master record if needed
 * - create market data if candidate market data exists
 * - create or reactivate a WATCHLIST UserBond
 * - mark the candidate as ADDED_TO_WATCHLIST
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
 * Ignored candidates disappear from the Discover Bonds page and should not be
 * shown again in future discovery runs.
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
 * The backend validates the file before replacing the existing CSV universe.
 * The old CSV remains unchanged if validation fails.
 *
 * Expected CSV field name:
 * - file
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