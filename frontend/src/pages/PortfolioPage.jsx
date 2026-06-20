/**
 * Portfolio page.
 *
 * Displays bonds owned by the user and backend-calculated portfolio-level
 * financial metrics using FX conversion into a selected base currency.
 *
 * This page also displays the Interest Rate Stress Test before the detailed
 * Portfolio Table. The stress test estimates how the portfolio value may change
 * under parallel yield shocks using modified duration.
 *
 * Important:
 *   FX rates are managed centrally from the FX Rates page.
 *   Portfolio only consumes already-stored FX data.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchPortfolio } from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
  formatRatioAsPercent,
} from "../utils/formatters";

const BASE_CURRENCY_OPTIONS = ["EUR", "USD", "GBP"];

function PortfolioPage() {
  const [portfolioData, setPortfolioData] = useState(null);
  const [baseCurrency, setBaseCurrency] = useState("EUR");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadPortfolio() {
      try {
        setErrorMessage("");

        const data = await fetchPortfolio(baseCurrency);
        setPortfolioData(data);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση του Portfolio.");
      }
    }

    loadPortfolio();
  }, [baseCurrency]);

  function handleBaseCurrencyChange(event) {
    setBaseCurrency(event.target.value);
  }

  if (errorMessage) {
    return <div className="error-box">{errorMessage}</div>;
  }

  if (!portfolioData) {
    return <div className="loading-text">Loading portfolio...</div>;
  }

  const rows = portfolioData.items || [];
  const summary = portfolioData.summary || {};
  const metrics = portfolioData.portfolio_metrics || {};
  const stressTest = portfolioData.interest_rate_stress_test || {};

  const portfolioBaseCurrency =
    metrics.portfolio_base_currency ||
    summary.portfolio_base_currency ||
    baseCurrency;

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>Portfolio</h1>
          <p>
            Χρηματοοικονομική εικόνα των ομολόγων που κατέχεις, με υπολογισμούς
            από το backend και FX conversion.
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
            to="/positions/new?type=PORTFOLIO"
            className="primary-link-button"
          >
            Add to Portfolio
          </Link>
        </div>
      </div>

      <Disclaimer text={portfolioData.disclaimer} />

      {metrics.mixed_currency_warning && (
        <div className="warning-box">{metrics.mixed_currency_warning}</div>
      )}

      <div className="summary-grid">
        <div className="summary-card">
          <span>Total Value ({portfolioBaseCurrency})</span>
          <strong>
            {formatMoney(summary.total_value, portfolioBaseCurrency, 2)}
          </strong>
        </div>

        <div className="summary-card">
          <span>Weighted Duration</span>
          <strong>{formatDecimal(summary.portfolio_duration, 2)}</strong>
        </div>

        <div className="summary-card">
          <span>Weighted Risk Score</span>
          <strong>{formatDecimal(summary.portfolio_risk_score, 2)}</strong>
        </div>

        <div className="summary-card">
          <span>Bonds</span>
          <strong>{summary.bond_count}</strong>
        </div>
      </div>

      <div className="portfolio-financial-grid">
        <FinancialMetricCard
          title="Weighted Avg YTM"
          value={formatPercent(metrics.weighted_average_ytm, 2)}
          description="Σταθμισμένη απόδοση έως τη λήξη με βάση το converted weight κάθε θέσης."
        />

        <FinancialMetricCard
          title="Weighted Current Yield"
          value={formatPercent(metrics.weighted_current_yield, 2)}
          description="Σταθμισμένη τρέχουσα απόδοση κουπονιού σε σχέση με την τιμή αγοράς."
        />

        <FinancialMetricCard
          title="Portfolio Concentration"
          value={formatRatioAsPercent(metrics.portfolio_concentration, 2)}
          description="Το μεγαλύτερο ποσοστό που κατέχει μία μόνο θέση στο Portfolio."
        />

        <FinancialMetricCard
          title="Est. Annual Coupon Income"
          value={formatMoney(
            metrics.estimated_annual_coupon_income,
            portfolioBaseCurrency,
            2
          )}
          description="Εκτιμώμενο ετήσιο καθαρό εισόδημα κουπονιών σε base currency."
        />
      </div>

      <div className="portfolio-insights-grid">
        <PortfolioInsightCard title="Top Position">
          {metrics.top_position ? (
            <PositionInsight
              item={metrics.top_position.item}
              metricLabel="Weight"
              metricValue={formatRatioAsPercent(metrics.top_position.weight, 2)}
            />
          ) : (
            <p className="muted-text">Δεν υπάρχει ακόμα θέση.</p>
          )}
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Highest Risk Position">
          {metrics.highest_risk_position ? (
            <PositionInsight
              item={metrics.highest_risk_position.item}
              metricLabel="Risk Score"
              metricValue={formatDecimal(
                metrics.highest_risk_position.risk_score,
                2
              )}
            />
          ) : (
            <p className="muted-text">Δεν υπάρχει ακόμα διαθέσιμο risk score.</p>
          )}
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Best Value Position">
          {metrics.best_value_position ? (
            <PositionInsight
              item={metrics.best_value_position.item}
              metricLabel="IV vs Market Price"
              metricValue={formatPercent(
                metrics.best_value_position.iv_vs_market_price,
                2
              )}
            />
          ) : (
            <p className="muted-text">Δεν υπάρχει ακόμα διαθέσιμο value metric.</p>
          )}
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Currency Exposure">
          <ExposureList
            items={metrics.currency_exposure}
            portfolioBaseCurrency={portfolioBaseCurrency}
            emptyMessage="Δεν υπάρχει ακόμα currency exposure."
          />
        </PortfolioInsightCard>
      </div>

      <InterestRateStressTestSection
        stressTest={stressTest}
        portfolioBaseCurrency={portfolioBaseCurrency}
      />

      <div className="table-card">
        <h2>Portfolio Table</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Bond</th>
                <th>ISIN</th>
                <th>Currency</th>
                <th>Original Value</th>
                <th>FX Rate</th>
                <th>Converted Value</th>
                <th>Weight</th>
                <th>YTM</th>
                <th>Current Yield</th>
                <th>Modified Duration</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Signal</th>
              </tr>
            </thead>

            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan="13">Δεν υπάρχουν ακόμα ομόλογα στο Portfolio.</td>
                </tr>
              ) : (
                rows.map((row) => {
                  const item = row.user_bond;
                  const bond = item.bond;
                  const analysis = item.latest_analysis;
                  const marketData = item.latest_market_data;

                  return (
                    <tr key={item.id}>
                      <td>
                        <Link to={`/positions/${item.id}`}>{bond.name}</Link>
                      </td>

                      <td>{bond.isin}</td>

                      <td>{bond.currency}</td>

                      <td>
                        {formatMoney(
                          row.original_position_value,
                          row.original_currency,
                          2
                        )}
                      </td>

                      <td>
                        {row.fx_rate_missing
                          ? "Missing"
                          : formatDecimal(row.fx_rate_to_base, 6)}
                      </td>

                      <td>
                        {row.fx_rate_missing
                          ? "-"
                          : formatMoney(
                              row.converted_position_value,
                              row.portfolio_base_currency,
                              2
                            )}
                      </td>

                      <td>{formatRatioAsPercent(row.weight, 2)}</td>

                      <td>{formatPercent(marketData?.ytm, 2)}</td>

                      <td>{formatPercent(analysis?.current_yield, 2)}</td>

                      <td>{formatDecimal(analysis?.modified_duration, 2)}</td>

                      <td>{formatDecimal(analysis?.risk_score, 2)}</td>

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

function FinancialMetricCard({ title, value, description }) {
  return (
    <div className="financial-metric-card">
      <span>{title}</span>
      <strong>{value || "-"}</strong>
      <p>{description}</p>
    </div>
  );
}

function PortfolioInsightCard({ title, children }) {
  return (
    <div className="portfolio-insight-card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

function PositionInsight({ item, metricLabel, metricValue }) {
  return (
    <div className="position-insight">
      <Link to={`/positions/${item.id}`}>{item.bond.name}</Link>
      <span>{item.bond.isin}</span>

      <div className="position-insight-metric">
        <span>{metricLabel}</span>
        <strong>{metricValue}</strong>
      </div>
    </div>
  );
}

function ExposureList({ items, portfolioBaseCurrency, emptyMessage }) {
  if (!items || items.length === 0) {
    return <p className="muted-text">{emptyMessage}</p>;
  }

  return (
    <div className="exposure-list">
      {items.map((item) => (
        <div className="exposure-row" key={item.currency}>
          <div>
            <strong>{item.currency}</strong>
            <span>
              {formatMoney(item.original_value, item.currency, 2)} →{" "}
              {formatMoney(item.converted_value, portfolioBaseCurrency, 2)}
            </span>
          </div>

          <span>{formatRatioAsPercent(item.weight, 2)}</span>
        </div>
      ))}
    </div>
  );
}

function InterestRateStressTestSection({
  stressTest,
  portfolioBaseCurrency,
}) {
  const scenarioRows = stressTest.scenario_rows || [];
  const positionRows = stressTest.position_rows || [];
  const excludedPositions = stressTest.excluded_positions || [];

  if (scenarioRows.length === 0) {
    return (
      <div className="table-card">
        <h2>Interest Rate Stress Test</h2>
        <p className="muted-text">
          Δεν υπάρχουν αρκετά δεδομένα για stress test. Χρειάζεται position
          value και modified duration.
        </p>
      </div>
    );
  }

  return (
    <div className="stress-test-section">
      <div className="page-header">
        <h1>Interest Rate Stress Test</h1>
        <p>
          Εκτίμηση μεταβολής αξίας Portfolio με βάση modified duration. Δεν
          περιλαμβάνει convexity, credit spread shocks ή FX shocks.
        </p>
      </div>

      {stressTest.disclaimer && (
        <div className="warning-box">{stressTest.disclaimer}</div>
      )}

      {stressTest.has_excluded_positions && (
        <div className="warning-box">
          Ορισμένες θέσεις εξαιρέθηκαν από το stress test επειδή λείπει
          duration, αξία θέσης ή FX rate.
        </div>
      )}

      <div className="stress-card-grid">
        <StressScenarioCard
          title="Best Scenario"
          scenario={stressTest.best_scenario}
          portfolioBaseCurrency={portfolioBaseCurrency}
        />

        <StressScenarioCard
          title="Worst Scenario"
          scenario={stressTest.worst_scenario}
          portfolioBaseCurrency={portfolioBaseCurrency}
        />

        <div className="stress-card">
          <span>Method</span>
          <strong>Modified Duration</strong>
          <p>{stressTest.method}</p>
        </div>
      </div>

      <div className="table-card">
        <h2>Portfolio Scenario Summary</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Estimated Portfolio Value</th>
                <th>Gain / Loss</th>
                <th>Gain / Loss %</th>
              </tr>
            </thead>

            <tbody>
              {scenarioRows.map((row) => (
                <tr key={row.scenario_label}>
                  <td>
                    <strong>{row.scenario_label}</strong>
                  </td>

                  <td>
                    {formatMoney(
                      row.estimated_portfolio_value,
                      portfolioBaseCurrency,
                      2
                    )}
                  </td>

                  <td className={getGainLossClass(row.gain_loss)}>
                    {formatMoney(row.gain_loss, portfolioBaseCurrency, 2)}
                  </td>

                  <td className={getGainLossClass(row.gain_loss)}>
                    {formatRatioAsPercent(row.gain_loss_percent, 2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="table-card">
        <h2>Per-Bond Interest Rate Impact</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Bond</th>
                <th>ISIN</th>
                <th>Current Value</th>
                <th>Modified Duration</th>
                <th>+1.00% Impact</th>
                <th>+2.00% Impact</th>
              </tr>
            </thead>

            <tbody>
              {positionRows.length === 0 ? (
                <tr>
                  <td colSpan="6">Δεν υπάρχουν διαθέσιμες θέσεις.</td>
                </tr>
              ) : (
                positionRows.map((row) => {
                  const onePercentImpact = findScenarioImpact(
                    row.scenario_impacts,
                    "+1.00%"
                  );
                  const twoPercentImpact = findScenarioImpact(
                    row.scenario_impacts,
                    "+2.00%"
                  );

                  return (
                    <tr key={row.user_bond_id}>
                      <td>{row.bond_name}</td>

                      <td>{row.isin}</td>

                      <td>
                        {formatMoney(
                          row.current_value,
                          portfolioBaseCurrency,
                          2
                        )}
                      </td>

                      <td>{formatDecimal(row.modified_duration, 2)}</td>

                      <td className={getGainLossClass(onePercentImpact?.gain_loss)}>
                        {formatMoney(
                          onePercentImpact?.gain_loss,
                          portfolioBaseCurrency,
                          2
                        )}
                      </td>

                      <td className={getGainLossClass(twoPercentImpact?.gain_loss)}>
                        {formatMoney(
                          twoPercentImpact?.gain_loss,
                          portfolioBaseCurrency,
                          2
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {excludedPositions.length > 0 && (
        <div className="table-card">
          <h2>Excluded Positions</h2>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Bond</th>
                  <th>ISIN</th>
                  <th>Reason</th>
                </tr>
              </thead>

              <tbody>
                {excludedPositions.map((position) => (
                  <tr key={position.isin}>
                    <td>{position.bond_name}</td>
                    <td>{position.isin}</td>
                    <td>{position.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StressScenarioCard({ title, scenario, portfolioBaseCurrency }) {
  if (!scenario) {
    return (
      <div className="stress-card">
        <span>{title}</span>
        <strong>-</strong>
      </div>
    );
  }

  return (
    <div className="stress-card">
      <span>{title}</span>
      <strong>{scenario.scenario_label}</strong>
      <p>
        {formatMoney(scenario.gain_loss, portfolioBaseCurrency, 2)} (
        {formatRatioAsPercent(scenario.gain_loss_percent, 2)})
      </p>
    </div>
  );
}

function findScenarioImpact(impacts, scenarioLabel) {
  if (!impacts) {
    return null;
  }

  return impacts.find((impact) => impact.scenario_label === scenarioLabel);
}

function getGainLossClass(value) {
  const numericValue = Number(value || 0);

  if (numericValue > 0) {
    return "positive-value";
  }

  if (numericValue < 0) {
    return "negative-value";
  }

  return "";
}

export default PortfolioPage;