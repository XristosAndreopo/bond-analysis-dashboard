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
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

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

          <Link className="secondary-button" to="/discover-bonds">
            Discover Bonds
          </Link>

          <Link className="primary-button" to="/positions/new?type=WATCHLIST">
            Add Bond
          </Link>
        </div>
      </div>

      <Disclaimer text={watchlistData?.disclaimer} />

      {errorMessage && <div className="error-box">{errorMessage}</div>}

      {metrics.fx_warning && (
        <div className="warning-box">
          {metrics.fx_warning}
        </div>
      )}

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
                    <td colSpan="12">
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
                          {formatPercent(
                            marketData?.market_required_return,
                            2
                          )}
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
            rate exists.
          </p>
        </div>
      )}
    </section>
  );
}

export default WatchlistPage;