/**
 * My Watchlist page.
 *
 * Displays bonds that the user is already monitoring before buying.
 *
 * This page is FX-aware because buy decisions can depend on currency.
 * Example:
 * - A USD bond may look attractive in USD terms.
 * - For a EUR-based user, the final decision also depends on USD/EUR.
 *
 * FX rates are updated from the central FX Rates page.
 *
 * Important:
 * - Discover Bonds shows only preliminary indications.
 * - Watchlist shows the full backend analysis.
 * - The discount rate shown here is the effective discount rate used by the
 *   backend analysis. If market_required_return is missing, the backend uses
 *   YTM as fallback.
 * - Update Prices uses AI-researched web data and keeps source/confidence
 *   metadata. It is not an official live market feed.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  fetchWatchlist,
  updateWatchlistMarketData,
} from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
} from "../utils/formatters";

const BASE_CURRENCY_OPTIONS = ["EUR", "USD", "GBP"];
const WATCHLIST_REFRESH_MAX_ITEMS = 12;

function WatchlistPage() {
  const [watchlistData, setWatchlistData] = useState(null);
  const [baseCurrency, setBaseCurrency] = useState("EUR");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingMarketData, setIsUpdatingMarketData] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [updateWarnings, setUpdateWarnings] = useState([]);
  const [updateErrors, setUpdateErrors] = useState([]);

  useEffect(() => {
    loadWatchlist();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseCurrency]);

  async function loadWatchlist() {
    setIsLoading(true);

    try {
      setErrorMessage("");

      const data = await fetchWatchlist(baseCurrency);
      setWatchlistData(data);
    } catch (error) {
      setErrorMessage("Could not load Watchlist data.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleBaseCurrencyChange(event) {
    setBaseCurrency(event.target.value);
  }

  async function handleUpdateMarketData() {
    setIsUpdatingMarketData(true);
    setErrorMessage("");
    setSuccessMessage("");
    setUpdateWarnings([]);
    setUpdateErrors([]);

    try {
      const result = await updateWatchlistMarketData(
        baseCurrency,
        WATCHLIST_REFRESH_MAX_ITEMS
      );

      const summary = result.import_summary || {};
      const createdCount = summary.total_created || 0;
      const updatedCount = summary.total_updated || 0;
      const skippedCount = summary.total_skipped || 0;

      setSuccessMessage(
        `Watchlist market data updated. Created: ${createdCount}, ` +
          `updated: ${updatedCount}, skipped: ${skippedCount}.`
      );
      setUpdateWarnings(result.warnings || []);
      setUpdateErrors(summary.errors || []);

      await loadWatchlist();
    } catch (error) {
      setErrorMessage(
        error?.response?.data?.detail ||
          "Could not update Watchlist market data."
      );
    } finally {
      setIsUpdatingMarketData(false);
    }
  }

  const rows = watchlistData?.items || [];
  const metrics = watchlistData?.watchlist_metrics || {};
  const portfolioBaseCurrency =
    metrics.portfolio_base_currency || baseCurrency;

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>My Watchlist</h1>
          <p>
            Bonds you already monitor before buying. All analysis and FX-aware
            values are calculated by the backend.
          </p>
        </div>

        <div className="portfolio-header-actions">
          <label className="compact-select-label">
            Base Currency
            <select value={baseCurrency} onChange={handleBaseCurrencyChange}>
              {BASE_CURRENCY_OPTIONS.map((currency) => (
                <option value={currency} key={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </label>

          <button
            className="secondary-button"
            type="button"
            onClick={handleUpdateMarketData}
            disabled={isUpdatingMarketData || rows.length === 0}
          >
            {isUpdatingMarketData ? "Updating prices..." : "Update Prices"}
          </button>

          <Link className="secondary-button" to="/discover-bonds">
            Discover Bonds
          </Link>

          <Link className="primary-button" to="/positions/new?type=WATCHLIST">
            Add Bond
          </Link>
        </div>
      </div>

      <Disclaimer text={watchlistData?.disclaimer} />

      <div className="warning-box">
        Η αξιολόγηση στο Watchlist είναι η πλήρης αξιολόγηση και μπορεί να
        διαφέρει από την προκαταρκτική ένδειξη του Discover Bonds, επειδή εδώ
        λαμβάνονται υπόψη όλα τα απαραίτητα στοιχεία.
      </div>

      <div className="info-box">
        Το κουμπί Update Prices χρησιμοποιεί AI-researched δημόσιες πηγές για
        ενημέρωση τιμών/YTM. Δεν είναι επίσημο live market feed. Έλεγχε πάντα
        Source, Confidence και Review status.
      </div>

      {errorMessage && <div className="error-box">{errorMessage}</div>}
      {successMessage && <div className="success-box">{successMessage}</div>}

      {updateWarnings.length > 0 && (
        <div className="warning-box">
          <strong>Research warnings:</strong>
          <ul className="compact-message-list">
            {updateWarnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {updateErrors.length > 0 && (
        <div className="warning-box">
          <strong>Import notes:</strong>
          <ul className="compact-message-list">
            {updateErrors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {metrics.fx_warning && <div className="warning-box">{metrics.fx_warning}</div>}

      {isLoading ? (
        <div className="loading-text">Loading watchlist...</div>
      ) : (
        <div className="table-card">
          <div className="section-header">
            <div>
              <h2>Monitored Bonds</h2>
              <p>
                Current market data, converted prices, risk levels and signals
                for bonds in your Watchlist.
              </p>
            </div>
          </div>

          <div className="table-scroll">
            <table className="wide-table">
              <thead>
                <tr>
                  <th>Bond</th>
                  <th>ISIN</th>
                  <th>Issuer</th>
                  <th>Currency</th>
                  <th>Market Price</th>
                  <th>FX Rate</th>
                  <th>Converted Price</th>
                  <th>YTM</th>
                  <th>Discount Rate</th>
                  <th>Source</th>
                  <th>Last Updated</th>
                  <th>Data Quality</th>
                  <th>Risk</th>
                  <th>Signal</th>
                  <th>Reasoning</th>
                </tr>
              </thead>

              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan="15">
                      There are no bonds in your Watchlist yet.
                    </td>
                  </tr>
                ) : (
                  rows.map((row) => {
                    const item = row.user_bond;
                    const bond = item.bond;
                    const marketData = item.latest_market_data;
                    const analysis = item.latest_analysis;

                    return (
                      <tr key={item.id}>
                        <td>
                          <Link to={`/positions/${item.id}`}>
                            {bond.name}
                          </Link>
                        </td>

                        <td>{bond.isin}</td>

                        <td>{bond.issuer}</td>

                        <td>{bond.currency}</td>

                        <td>
                          {row.original_market_price
                            ? formatMoney(
                                row.original_market_price,
                                row.original_currency,
                                4
                              )
                            : "-"}
                        </td>

                        <td>
                          {row.fx_rate_missing
                            ? "Missing"
                            : formatDecimal(row.fx_rate_to_base, 6)}
                        </td>

                        <td>
                          {row.converted_market_price
                            ? formatMoney(
                                row.converted_market_price,
                                row.portfolio_base_currency,
                                4
                              )
                            : "-"}
                        </td>

                        <td>{formatPercent(marketData?.ytm, 2)}</td>

                        <td>
                          <DiscountRateCell marketData={marketData} />
                        </td>

                        <td>
                          <MarketDataSourceCell marketData={marketData} />
                        </td>

                        <td>{formatDateTime(marketData?.retrieved_at)}</td>

                        <td>
                          <DataQualityCell marketData={marketData} />
                        </td>

                        <td>
                          <RiskBadge
                            riskLevel={analysis?.risk_level}
                            label={analysis?.risk_level_label}
                          />
                        </td>

                        <td>
                          <SignalBadge
                            signal={analysis?.final_signal}
                            label={analysis?.final_signal_label}
                          />
                        </td>

                        <td>{analysis?.reasoning || "-"}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <p className="helper-text">
            Converted prices use {portfolioBaseCurrency} when the required FX
            rate exists. The Discount Rate column shows the effective rate used
            by the backend analysis. If Market Required Return is missing, YTM
            is used as fallback.
          </p>
        </div>
      )}
    </section>
  );
}

function DiscountRateCell({ marketData }) {
  /**
   * Show the effective discount rate used by the backend analysis.
   *
   * Backend rule:
   * 1. market_required_return
   * 2. ytm fallback
   * 3. empty if both are missing
   */
  if (!marketData?.effective_discount_rate) {
    return "-";
  }

  return (
    <>
      {formatPercent(marketData.effective_discount_rate, 2)}
      <br />
      <small>{getDiscountRateSourceLabel(marketData)}</small>
    </>
  );
}

function MarketDataSourceCell({ marketData }) {
  /**
   * Display the source for latest market data.
   */
  if (!marketData) {
    return "-";
  }

  const sourceLabel = marketData.source || marketData.data_origin_label || "Source";

  if (!marketData.source_url) {
    return sourceLabel;
  }

  return (
    <a href={marketData.source_url} target="_blank" rel="noreferrer">
      {sourceLabel}
    </a>
  );
}

function DataQualityCell({ marketData }) {
  /**
   * Display confidence and review status for AI-researched data.
   */
  if (!marketData) {
    return "-";
  }

  const confidence = marketData.confidence_label || marketData.confidence || "-";
  const reviewStatus =
    marketData.review_status_label || marketData.review_status || "-";

  return (
    <div className="data-quality-cell">
      <strong>{confidence}</strong>
      <span>{reviewStatus}</span>
      {marketData.needs_review && <small>Needs review</small>}
    </div>
  );
}

function getDiscountRateSourceLabel(marketData) {
  /**
   * Return a small explanation for the discount rate source.
   */
  if (marketData?.market_required_return) {
    return "Market required return";
  }

  if (marketData?.ytm) {
    return "YTM fallback";
  }

  return "No rate source";
}

function formatDateTime(value) {
  /**
   * Format ISO date/datetime values safely for display.
   */
  if (!value) {
    return "-";
  }

  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return parsedDate.toLocaleString();
}

export default WatchlistPage;
