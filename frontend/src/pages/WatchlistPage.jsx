/**
 * Watchlist page.
 *
 * Displays bonds monitored by the user but not currently owned.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchWatchlist } from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import { formatDecimal, formatPercent } from "../utils/formatters";

function WatchlistPage() {
  const [watchlistData, setWatchlistData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadWatchlist() {
      try {
        const data = await fetchWatchlist();
        setWatchlistData(data);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση της Watchlist.");
      }
    }

    loadWatchlist();
  }, []);

  if (errorMessage) {
    return <div className="error-box">{errorMessage}</div>;
  }

  if (!watchlistData) {
    return <div className="loading-text">Loading watchlist...</div>;
  }

  const items = watchlistData.items || [];

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>Watchlist</h1>
          <p>Ομόλογα που παρακολουθείς αλλά δεν έχεις αγοράσει ακόμα.</p>
        </div>

        <Link to="/positions/new?type=WATCHLIST" className="primary-link-button">
          Add to Watchlist
        </Link>
      </div>

      <Disclaimer text={watchlistData.disclaimer} />

      <div className="table-card">
        <h2>Watchlist Table</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Bond</th>
                <th>ISIN</th>
                <th>Market Price</th>
                <th>Market Required Return</th>
                <th>YTM</th>
                <th>Risk Level</th>
                <th>Risk Score</th>
                <th>Signal</th>
                <th>Reasoning</th>
              </tr>
            </thead>

            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="9">Δεν υπάρχουν ακόμα ομόλογα στη Watchlist.</td>
                </tr>
              ) : (
                items.map((item) => {
                  const marketData = item.latest_market_data;
                  const analysis = item.latest_analysis;

                  return (
                    <tr key={item.id}>
                      <td>
                        <Link to={`/positions/${item.id}`}>
                          {item.bond.name}
                        </Link>
                      </td>
                      <td>{item.bond.isin}</td>
                      <td>
                        {formatDecimal(marketData?.market_price, 4)}
                      </td>
                      <td>
                        {formatPercent(
                          marketData?.market_required_return,
                          2
                        )}
                      </td>
                      <td>{formatPercent(marketData?.ytm, 2)}</td>
                      <td>
                        <RiskBadge
                          riskLevel={analysis?.risk_level}
                          label={analysis?.risk_level_label}
                        />
                      </td>
                      <td>{formatDecimal(analysis?.risk_score, 2)}</td>
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