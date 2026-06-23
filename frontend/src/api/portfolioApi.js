
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
 * @param {string} baseCurrency - Portfolio base currency.
 * @returns {Promise<object>} Portfolio data.
 */
export async function fetchPortfolio(baseCurrency = "EUR") {
  const response = await apiClient.get("/portfolio/", {
    params: {
      base_currency: baseCurrency,
    },
  });

  return response.data;
}

/**
 * Refresh market data for active Portfolio bonds through backend AI research.
 *
 * The backend researches only ISINs that already exist in the authenticated
 * user's active Portfolio. It imports valid BondMarketData rows and keeps
 * source/confidence/review metadata.
 *
 * @param {string} baseCurrency - Selected base currency for context.
 * @param {number} maxItems - Maximum Portfolio ISINs to refresh in one run.
 * @returns {Promise<object>} Refresh result.
 */
export async function updatePortfolioMarketData(
  baseCurrency = "EUR",
  maxItems = 12
) {
  const response = await apiClient.post(
    "/ai-research/portfolio-market-refresh/",
    {
      base_currency: baseCurrency,
      max_items: maxItems,
    }
  );

  return response.data;
}

/**
 * Fetch watchlist data for the authenticated user.
 *
 * @param {string} baseCurrency - Selected base currency for FX conversion.
 * @returns {Promise<object>} Watchlist data.
 */
export async function fetchWatchlist(baseCurrency = "EUR") {
  const response = await apiClient.get("/watchlist/", {
    params: {
      base_currency: baseCurrency,
    },
  });

  return response.data;
}

/**
 * Refresh market data for active Watchlist bonds through backend AI research.
 *
 * The backend researches only ISINs that already exist in the authenticated
 * user's active Watchlist. It imports valid BondMarketData rows and keeps
 * source/confidence/review metadata.
 *
 * @param {string} baseCurrency - Selected base currency for context.
 * @param {number} maxItems - Maximum Watchlist ISINs to refresh in one run.
 * @returns {Promise<object>} Refresh result.
 */
export async function updateWatchlistMarketData(
  baseCurrency = "EUR",
  maxItems = 12
) {
  const response = await apiClient.post(
    "/ai-research/watchlist-market-refresh/",
    {
      base_currency: baseCurrency,
      max_items: maxItems,
    }
  );

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

