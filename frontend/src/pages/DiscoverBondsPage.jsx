/**
 * Discover Bonds page.
 *
 * Displays bond candidates produced by the backend discovery engine.
 *
 * The frontend does not invent bond data. It only:
 * - asks the backend to run discovery
 * - displays validated candidates
 * - displays backend-calculated preview risk/signal
 * - sends Add to Watchlist or Ignore actions
 *
 * The backend remains responsible for provider data, validation, rating
 * filtering, maturity filtering, duplicate checks, user ownership rules,
 * and preview signal calculation.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  addDiscoveredBondToWatchlist,
  fetchDiscoveredBonds,
  ignoreDiscoveredBond,
  runBondDiscovery,
} from "../api/discoveryApi";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
} from "../utils/formatters";

function DiscoverBondsPage() {
  const [candidates, setCandidates] = useState([]);
  const [lastDiscoveryRun, setLastDiscoveryRun] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState(false);
  const [candidateActionId, setCandidateActionId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    loadCandidates();
  }, []);

  async function loadCandidates() {
    setIsLoading(true);

    try {
      setErrorMessage("");

      const data = await fetchDiscoveredBonds();
      setCandidates(Array.isArray(data) ? data : []);
    } catch (error) {
      setErrorMessage("Could not load discovered bond candidates.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRunDiscovery() {
    setIsRunningDiscovery(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const result = await runBondDiscovery();

      setLastDiscoveryRun(result.run || null);
      setCandidates(Array.isArray(result.candidates) ? result.candidates : []);
      setSuccessMessage("Discovery completed successfully.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not run bond discovery.")
      );
    } finally {
      setIsRunningDiscovery(false);
    }
  }

  async function handleAddToWatchlist(candidateId) {
    setCandidateActionId(candidateId);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      await addDiscoveredBondToWatchlist(candidateId);
      await loadCandidates();

      setSuccessMessage("Candidate added to My Watchlist.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not add candidate to Watchlist.")
      );
    } finally {
      setCandidateActionId(null);
    }
  }

  async function handleIgnore(candidateId) {
    setCandidateActionId(candidateId);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      await ignoreDiscoveredBond(candidateId);
      await loadCandidates();

      setSuccessMessage("Candidate ignored.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not ignore candidate.")
      );
    } finally {
      setCandidateActionId(null);
    }
  }

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>Discover Bonds</h1>
          <p>
            Find validated bond candidates from backend providers and add them
            to your Watchlist for further analysis.
          </p>
        </div>

        <div className="portfolio-header-actions">
          <Link className="secondary-button" to="/watchlist">
            My Watchlist
          </Link>

          <button
            type="button"
            className="primary-button"
            onClick={handleRunDiscovery}
            disabled={isRunningDiscovery}
          >
            {isRunningDiscovery ? "Running..." : "Run Discovery"}
          </button>
        </div>
      </div>

      <div className="disclaimer-box">
        Discovery candidates are educational analytical data only. They are not
        investment advice and they do not represent a recommendation to buy or
        sell securities.
      </div>

      {errorMessage && <div className="error-box">{errorMessage}</div>}
      {successMessage && <div className="success-box">{successMessage}</div>}

      {lastDiscoveryRun && (
        <div className="summary-card-grid">
          <DiscoveryRunCard title="Found" value={lastDiscoveryRun.total_found} />
          <DiscoveryRunCard title="Saved" value={lastDiscoveryRun.total_saved} />
          <DiscoveryRunCard
            title="Skipped"
            value={lastDiscoveryRun.total_skipped}
          />
          <DiscoveryRunCard
            title="Status"
            value={lastDiscoveryRun.status_label || lastDiscoveryRun.status}
          />
        </div>
      )}

      <div className="table-card">
        <div className="section-header section-header-with-actions">
          <div>
            <h2>Candidate Bonds</h2>
            <p>
              The backend excludes expired bonds, ratings below the selected
              minimum threshold, duplicate ISINs, and bonds already active in
              your Portfolio or Watchlist.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="loading-text">Loading discovered bonds...</div>
        ) : (
          <div className="table-scroll">
            <table className="wide-table">
              <thead>
                <tr>
                  <th>Bond</th>
                  <th>ISIN</th>
                  <th>Country</th>
                  <th>Issuer</th>
                  <th>Currency</th>
                  <th>Rating</th>
                  <th>Maturity</th>
                  <th>Coupon</th>
                  <th>Market Price</th>
                  <th>YTM</th>
                  <th>Duration</th>
                  <th>Preview Risk</th>
                  <th>Preview Signal</th>
                  <th>Reasoning</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td colSpan="15">
                      No candidates are available. Press Run Discovery.
                    </td>
                  </tr>
                ) : (
                  candidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td>{candidate.name}</td>

                      <td>{candidate.isin}</td>

                      <td>{candidate.country || "-"}</td>

                      <td>{candidate.issuer}</td>

                      <td>{candidate.currency}</td>

                      <td>{candidate.credit_rating}</td>

                      <td>{candidate.maturity_date}</td>

                      <td>{formatPercent(candidate.coupon_rate, 3)}</td>

                      <td>
                        {candidate.market_price
                          ? formatMoney(
                              candidate.market_price,
                              candidate.currency,
                              4
                            )
                          : "-"}
                      </td>

                      <td>{formatPercent(candidate.ytm, 2)}</td>

                      <td>{formatDecimal(candidate.duration, 4)}</td>

                      <td>
                        <RiskBadge
                          riskLevel={candidate.preview_risk_level}
                          label={candidate.preview_risk_label}
                        />
                      </td>

                      <td>
                        <SignalBadge
                          signal={candidate.preview_signal}
                          label={candidate.preview_signal_label}
                        />
                      </td>

                      <td>
                        {candidate.preview_reasoning ||
                          candidate.ai_reasoning ||
                          candidate.ai_summary ||
                          "Passes backend discovery filters. Review issuer risk, liquidity, duration, yield and currency exposure."}
                      </td>

                      <td>
                        <div className="table-action-buttons">
                          <button
                            type="button"
                            className="primary-button small-button"
                            disabled={candidateActionId === candidate.id}
                            onClick={() => handleAddToWatchlist(candidate.id)}
                          >
                            {candidateActionId === candidate.id
                              ? "Adding..."
                              : "Add"}
                          </button>

                          <button
                            type="button"
                            className="secondary-button small-button"
                            disabled={candidateActionId === candidate.id}
                            onClick={() => handleIgnore(candidate.id)}
                          >
                            Ignore
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function DiscoveryRunCard({ title, value }) {
  return (
    <div className="summary-card">
      <span>{title}</span>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}

function getApiErrorMessage(error, fallbackMessage) {
  /**
   * Extract a safe API error message for user-facing alerts.
   */
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.non_field_errors?.[0] ||
    fallbackMessage
  );
}

export default DiscoverBondsPage;