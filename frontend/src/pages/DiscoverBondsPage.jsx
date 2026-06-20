/**
 * Discover Bonds page.
 *
 * Displays bond candidates produced by the backend discovery engine.
 *
 * The frontend does not invent bond data. It only:
 * - lets the user choose discovery filters
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

const SOURCE_OPTIONS = [
  { value: "static_provider", label: "Static Provider" },
  { value: "csv_provider", label: "CSV Provider" },
];

const MINIMUM_RATING_OPTIONS = [
  "BBB-",
  "BBB",
  "BBB+",
  "A-",
  "A",
  "A+",
  "AA-",
  "AA",
  "AA+",
  "AAA",
];

const CURRENCY_OPTIONS = [
  { value: "", label: "All currencies" },
  { value: "EUR", label: "EUR" },
  { value: "USD", label: "USD" },
  { value: "GBP", label: "GBP" },
];

const COUNTRY_OPTIONS = [
  { value: "", label: "All countries" },
  { value: "GR", label: "Greece" },
  { value: "US", label: "United States" },
  { value: "DE", label: "Germany" },
  { value: "FR", label: "France" },
  { value: "IT", label: "Italy" },
  { value: "ES", label: "Spain" },
  { value: "NL", label: "Netherlands" },
];

const DEFAULT_FILTERS = {
  source: "static_provider",
  minRating: "BBB-",
  currency: "",
  country: "",
};

function DiscoverBondsPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
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

  function handleFilterChange(event) {
    const { name, value } = event.target;

    setFilters((currentFilters) => ({
      ...currentFilters,
      [name]: value,
    }));
  }

  function handleResetFilters() {
    setFilters(DEFAULT_FILTERS);
  }

  function buildDiscoveryPayload() {
    return {
      source: filters.source,
      min_rating: filters.minRating,
      currencies: filters.currency ? [filters.currency] : [],
      countries: filters.country ? [filters.country] : [],
    };
  }

  async function handleRunDiscovery() {
    setIsRunningDiscovery(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const result = await runBondDiscovery(buildDiscoveryPayload());

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
        </div>
      </div>

      <div className="disclaimer-box">
        Discovery candidates are educational analytical data only. They are not
        investment advice and they do not represent a recommendation to buy or
        sell securities.
      </div>

      <div className="toolbar-card">
        <div className="section-header">
          <div>
            <h2>Discovery Filters</h2>
            <p>
              Choose the source, minimum rating, currency and country filters
              before running discovery.
            </p>
          </div>
        </div>

        <div className="form-grid">
          <label>
            Source
            <select
              name="source"
              value={filters.source}
              onChange={handleFilterChange}
            >
              {SOURCE_OPTIONS.map((source) => (
                <option value={source.value} key={source.value}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Minimum Rating
            <select
              name="minRating"
              value={filters.minRating}
              onChange={handleFilterChange}
            >
              {MINIMUM_RATING_OPTIONS.map((rating) => (
                <option value={rating} key={rating}>
                  {rating}
                </option>
              ))}
            </select>
          </label>

          <label>
            Currency
            <select
              name="currency"
              value={filters.currency}
              onChange={handleFilterChange}
            >
              {CURRENCY_OPTIONS.map((currency) => (
                <option value={currency.value} key={currency.value}>
                  {currency.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Country
            <select
              name="country"
              value={filters.country}
              onChange={handleFilterChange}
            >
              {COUNTRY_OPTIONS.map((country) => (
                <option value={country.value} key={country.value}>
                  {country.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="primary-button"
            onClick={handleRunDiscovery}
            disabled={isRunningDiscovery}
          >
            {isRunningDiscovery ? "Running..." : "Run Discovery"}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={handleResetFilters}
            disabled={isRunningDiscovery}
          >
            Reset Filters
          </button>
        </div>
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
                      No candidates are available. Adjust filters or press Run
                      Discovery.
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