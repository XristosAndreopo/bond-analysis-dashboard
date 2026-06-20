/**
 * Portfolio page.
 *
 * Displays bonds owned by the user and backend-calculated portfolio-level
 * financial metrics using FX conversion into a selected base currency.
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
  const summary = portfolioData.summary;
  const metrics = portfolioData.portfolio_metrics || {};
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

      <div className="portfolio-insights-grid">
        <PortfolioInsightCard title="Annual Coupon Income by Currency">
          <CouponIncomeList
            items={metrics.estimated_annual_coupon_income_by_currency}
            portfolioBaseCurrency={portfolioBaseCurrency}
            emptyMessage="Δεν υπάρχει ακόμα εκτιμώμενο εισόδημα κουπονιών."
          />
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Signal Distribution">
          <DistributionList
            items={metrics.signal_distribution}
            emptyMessage="Δεν υπάρχουν ακόμα signals."
          />
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Risk Distribution">
          <DistributionList
            items={metrics.risk_distribution}
            emptyMessage="Δεν υπάρχουν ακόμα risk levels."
          />
        </PortfolioInsightCard>

        <PortfolioInsightCard title="Portfolio Risk Level">
          <div className="position-insight-metric">
            <span>Risk Level</span>
            <strong>{summary.portfolio_risk_level_label || "-"}</strong>
          </div>
        </PortfolioInsightCard>
      </div>

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
              {formatMoney(
                item.converted_value,
                portfolioBaseCurrency,
                2
              )}
            </span>
          </div>

          <span>{formatRatioAsPercent(item.weight, 2)}</span>
        </div>
      ))}
    </div>
  );
}

function CouponIncomeList({ items, portfolioBaseCurrency, emptyMessage }) {
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
              {formatMoney(
                item.converted_value,
                portfolioBaseCurrency,
                2
              )}
            </span>
          </div>

          <span>Annual coupon</span>
        </div>
      ))}
    </div>
  );
}

function DistributionList({ items, emptyMessage }) {
  if (!items || items.length === 0) {
    return <p className="muted-text">{emptyMessage}</p>;
  }

  return (
    <div className="exposure-list">
      {items.map((item) => (
        <div className="exposure-row" key={item.key}>
          <div>
            <strong>{item.label}</strong>
            <span>{item.key}</span>
          </div>

          <span>{item.count}</span>
        </div>
      ))}
    </div>
  );
}

export default PortfolioPage;