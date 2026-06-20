/**
 * Watchlist page.
 *
 * Displays bonds that the user is monitoring before buying.
 *
 * This page is FX-aware because buy decisions can depend on currency.
 * Example:
 * - A USD bond may look attractive in USD terms.
 * - For a EUR-based user, the final decision also depends on USD/EUR.
 *
 * FX rates are updated from the central FX Rates page.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchWatchlist } from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
} from "../utils/formatters";

const BASE_CURRENCY_OPTIONS = ["EUR", "USD", "GBP"];

function WatchlistPage() {
  const [watchlistData, setWatchlistData] = useState(null);
  const [baseCurrency, setBaseCurrency] = useState("EUR");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadWatchlist() {
      try {
        setErrorMessage("");

        const data = await fetchWatchlist(baseCurrency);
        setWatchlistData(data);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση του Watchlist.");
      }
    }

    loadWatchlist();
  }, [baseCurrency]);

  function handleBaseCurrencyChange(event) {
    setBaseCurrency(event.target.value);
  }

  if (errorMessage) {
    return <div className="error-box">{errorMessage}</div>;
  }

  if (!watchlistData) {
    return <div className="loading-text">Loading watchlist...</div>;
  }

  const rows = watchlistData.items || [];
  const metrics = watchlistData.watchlist_metrics || {};
  const portfolioBaseCurrency =
    metrics.portfolio_base_currency || baseCurrency;

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>Watchlist</h1>
          <p>
            Ομόλογα που παρακολουθείς πριν από πιθανή αγορά, με FX-aware τιμές
            για καλύτερη απόφαση.
          </p>
        </div>

        <div className="portfolio-header-actions">
          <label className="compact-select-label">
            Base Currency
            <select value={baseCurrency} onChange={handleBaseCurrencyChange}>
              {BASE_CURRENCY_OPTIONS.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </label>

          <Link
            to="/positions/new?type=WATCHLIST"
            className="primary-link-button"
          >
            Add to Watchlist
          </Link>
        </div>
      </div>

      <Disclaimer text={watchlistData.disclaimer} />

      {metrics.fx_warning && (
        <div className="warning-box">{metrics.fx_warning}</div>
      )}

      <div className="summary-grid">
        <div className="summary-card">
          <span>Watchlist Bonds</span>
          <strong>{metrics.watchlist_count || 0}</strong>
        </div>

        <div className="summary-card">
          <span>Base Currency</span>
          <strong>{portfolioBaseCurrency}</strong>
        </div>

        <div className="summary-card">
          <span>Missing FX Rates</span>
          <strong>{metrics.has_missing_fx_rates ? "Yes" : "No"}</strong>
        </div>

        <div className="summary-card">
          <span>FX Management</span>
          <Link to="/fx-rates">Open FX Rates</Link>
        </div>
      </div>

      <div className="table-card">
        <h2>Watchlist Table</h2>

        <div className="table-scroll">
          <table>
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
                <th>Required Return</th>
                <th>Risk</th>
                <th>Signal</th>
                <th>Reasoning</th>
              </tr>
            </thead>

            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan="12">Δεν υπάρχουν ακόμα ομόλογα στο Watchlist.</td>
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
                        <Link to={`/positions/${item.id}`}>{bond.name}</Link>
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
                        {formatPercent(marketData?.market_required_return, 2)}
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
      </div>
    </section>
  );
}

export default WatchlistPage;