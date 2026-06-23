/**
 * Dashboard page.
 *
 * For authenticated users:
 * - shows a quick overview of Portfolio bonds
 * - displays signal/risk distributions
 * - displays top risk and best value bond
 *
 * For unauthenticated visitors:
 * - shows a public dashboard preview without private data
 * - offers Login and Create Account actions
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchDashboard } from "../api/portfolioApi";
import { isAuthenticated } from "../auth/authService";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import { formatDecimal, formatMoney, formatPercent } from "../utils/formatters";

function DashboardPage() {
  const authenticated = isAuthenticated();

  const [dashboardData, setDashboardData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      if (!authenticated) {
        return;
      }

      try {
        const data = await fetchDashboard();
        setDashboardData(data);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση του Dashboard.");
      }
    }

    loadDashboard();
  }, [authenticated]);

  const dashboardInsights = useMemo(() => {
    if (!dashboardData) {
      return {
        signalDistribution: [],
        riskDistribution: [],
        topRiskItem: null,
        bestValueItem: null,
      };
    }

    const portfolioItems = dashboardData.portfolio_items || [];

    return {
      signalDistribution: buildSignalDistribution(portfolioItems),
      riskDistribution: buildRiskDistribution(portfolioItems),
      topRiskItem: getTopRiskItem(portfolioItems),
      bestValueItem: getBestValueItem(portfolioItems),
    };
  }, [dashboardData]);

  if (!authenticated) {
    return <PublicDashboardPreview />;
  }

  if (errorMessage) {
    return <div className="error-box">{errorMessage}</div>;
  }

  if (!dashboardData) {
    return <div className="loading-text">Loading dashboard...</div>;
  }

  const summary = dashboardData.summary;
  const portfolioItems = dashboardData.portfolio_items || [];

  return (
    <section className="page-section">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Γρήγορη εικόνα χαρτοφυλακίου, ρίσκου και αναλυτικών ενδείξεων.</p>
      </div>

      <Disclaimer text={dashboardData.disclaimer} />

      <div className="summary-grid">
        <div className="summary-card">
          <span>Total Value</span>
          <strong>{formatMoney(summary.total_value, "", 2)}</strong>
        </div>

        <div className="summary-card">
          <span>Portfolio Duration</span>
          <strong>{formatDecimal(summary.portfolio_duration, 2)}</strong>
        </div>

        <div className="summary-card">
          <span>Portfolio Risk</span>
          <strong>{formatDecimal(summary.portfolio_risk_score, 2)}</strong>
        </div>

        <div className="summary-card">
          <span>Risk Level</span>
          <strong>{summary.portfolio_risk_level_label || "-"}</strong>
        </div>
      </div>

      <div className="dashboard-insights-grid">
        <InsightCard title="Signal Distribution">
          <DistributionList
            items={dashboardInsights.signalDistribution}
            emptyMessage="Δεν υπάρχουν ακόμα signals."
          />
        </InsightCard>

        <InsightCard title="Risk Distribution">
          <DistributionList
            items={dashboardInsights.riskDistribution}
            emptyMessage="Δεν υπάρχουν ακόμα risk levels."
          />
        </InsightCard>

        <InsightCard title="Top Risk Bond">
          {dashboardInsights.topRiskItem ? (
            <BondInsight
              item={dashboardInsights.topRiskItem}
              metricLabel="Risk Score"
              metricValue={formatDecimal(
                dashboardInsights.topRiskItem.latest_analysis?.risk_score,
                2
              )}
            />
          ) : (
            <p className="muted-text">Δεν υπάρχει ακόμα διαθέσιμο ομόλογο.</p>
          )}
        </InsightCard>

        <InsightCard title="Best Value Bond">
          {dashboardInsights.bestValueItem ? (
            <BondInsight
              item={dashboardInsights.bestValueItem}
              metricLabel="IV vs Market Price"
              metricValue={formatPercent(
                dashboardInsights.bestValueItem.latest_analysis
                  ?.iv_vs_market_price,
                2
              )}
            />
          ) : (
            <p className="muted-text">Δεν υπάρχει ακόμα διαθέσιμο ομόλογο.</p>
          )}
        </InsightCard>
      </div>

      <div className="table-card">
        <h2>Portfolio Bonds</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Bond</th>
                <th>ISIN</th>
                <th>Risk Level</th>
                <th>Risk Score</th>
                <th>Signal</th>
                <th>Reasoning</th>
              </tr>
            </thead>

            <tbody>
              {portfolioItems.length === 0 ? (
                <tr>
                  <td colSpan="6">Δεν υπάρχουν ακόμα ομόλογα στο Portfolio.</td>
                </tr>
              ) : (
                portfolioItems.map((item) => {
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

function PublicDashboardPreview() {
  return (
    <main className="public-dashboard-page">
      <section className="public-dashboard-hero">
        <div className="public-dashboard-nav">
          <Link className="auth-logo-link" to="/dashboard">
            <span className="auth-logo-mark">B</span>
            <span>Bond Analysis Dashboard</span>
          </Link>

          <div className="public-dashboard-nav-actions">
            <Link className="secondary-link-button" to="/login">
              Login
            </Link>
            <Link className="primary-link-button" to="/signup">
              Create account
            </Link>
          </div>
        </div>

        <div className="public-dashboard-content">
          <span className="auth-hero-pill">Public preview</span>
          <h1>Analyze bonds, track risk and build your watchlist.</h1>
          <p>
            Συνδέσου για να δεις πραγματικά δεδομένα Portfolio, Watchlist,
            Discovery candidates και αναλυτικά risk signals.
          </p>

          <div className="public-dashboard-actions">
            <Link className="primary-link-button" to="/login">
              Login to your dashboard
            </Link>
            <Link className="secondary-link-button" to="/signup">
              Create free account
            </Link>
          </div>
        </div>
      </section>

      <section className="public-dashboard-preview-section">
        <div className="summary-grid public-summary-grid">
          <PreviewSummaryCard label="Portfolio Value" value="—" />
          <PreviewSummaryCard label="Portfolio Duration" value="—" />
          <PreviewSummaryCard label="Risk Level" value="—" />
          <PreviewSummaryCard label="Watchlist Bonds" value="—" />
        </div>

        <div className="dashboard-insights-grid">
          <InsightCard title="Portfolio Preview">
            <div className="public-preview-list">
              <PreviewRow label="Risk signals" value="Login required" />
              <PreviewRow label="Bond analysis" value="Private data" />
              <PreviewRow label="Market data" value="Protected" />
            </div>
          </InsightCard>

          <InsightCard title="What you can do">
            <div className="public-preview-list">
              <PreviewRow label="Track portfolio bonds" value="✓" />
              <PreviewRow label="Use AI discovery" value="✓" />
              <PreviewRow label="Build a watchlist" value="✓" />
            </div>
          </InsightCard>
        </div>

        <div className="disclaimer-box">
          This dashboard is for educational and analytical purposes only. It is
          not financial advice.
        </div>
      </section>
    </main>
  );
}

function PreviewSummaryCard({ label, value }) {
  return (
    <div className="summary-card public-preview-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>Available after login</small>
    </div>
  );
}

function PreviewRow({ label, value }) {
  return (
    <div className="distribution-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

/**
 * Build signal distribution from Portfolio items.
 *
 * @param {Array} items - Portfolio items.
 * @returns {Array} Distribution rows.
 */
function buildSignalDistribution(items) {
  const distributionMap = new Map();

  items.forEach((item) => {
    const analysis = item.latest_analysis;
    const signal = analysis?.final_signal || "REVIEW";
    const label = analysis?.final_signal_label || "Επανεξέταση";

    const currentCount = distributionMap.get(signal)?.count || 0;

    distributionMap.set(signal, {
      key: signal,
      label,
      count: currentCount + 1,
    });
  });

  return Array.from(distributionMap.values());
}

/**
 * Build risk distribution from Portfolio items.
 *
 * @param {Array} items - Portfolio items.
 * @returns {Array} Distribution rows.
 */
function buildRiskDistribution(items) {
  const distributionMap = new Map();

  items.forEach((item) => {
    const analysis = item.latest_analysis;
    const riskLevel = analysis?.risk_level || "UNKNOWN";
    const label = analysis?.risk_level_label || "Άγνωστο";

    const currentCount = distributionMap.get(riskLevel)?.count || 0;

    distributionMap.set(riskLevel, {
      key: riskLevel,
      label,
      count: currentCount + 1,
    });
  });

  return Array.from(distributionMap.values());
}

/**
 * Return the Portfolio item with the highest risk score.
 *
 * @param {Array} items - Portfolio items.
 * @returns {object|null} Portfolio item or null.
 */
function getTopRiskItem(items) {
  const itemsWithRisk = items.filter((item) => {
    const riskScore = Number(item.latest_analysis?.risk_score);

    return !Number.isNaN(riskScore);
  });

  if (itemsWithRisk.length === 0) {
    return null;
  }

  return itemsWithRisk.reduce((highestRiskItem, currentItem) => {
    const highestRiskScore = Number(highestRiskItem.latest_analysis.risk_score);
    const currentRiskScore = Number(currentItem.latest_analysis.risk_score);

    return currentRiskScore > highestRiskScore
      ? currentItem
      : highestRiskItem;
  });
}

/**
 * Return the Portfolio item with the highest IV vs Market Price value.
 *
 * This gives a simple "best theoretical value" indication based on the
 * application calculation. It is not an investment recommendation.
 *
 * @param {Array} items - Portfolio items.
 * @returns {object|null} Portfolio item or null.
 */
function getBestValueItem(items) {
  const itemsWithValueMetric = items.filter((item) => {
    const ivVsMarketPrice = Number(item.latest_analysis?.iv_vs_market_price);

    return !Number.isNaN(ivVsMarketPrice);
  });

  if (itemsWithValueMetric.length === 0) {
    return null;
  }

  return itemsWithValueMetric.reduce((bestValueItem, currentItem) => {
    const bestValue = Number(bestValueItem.latest_analysis.iv_vs_market_price);
    const currentValue = Number(currentItem.latest_analysis.iv_vs_market_price);

    return currentValue > bestValue ? currentItem : bestValueItem;
  });
}

function InsightCard({ title, children }) {
  return (
    <div className="insight-card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

function DistributionList({ items, emptyMessage }) {
  if (!items || items.length === 0) {
    return <p className="muted-text">{emptyMessage}</p>;
  }

  return (
    <div className="distribution-list">
      {items.map((item) => (
        <div className="distribution-row" key={item.key}>
          <span>{item.label}</span>
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

function BondInsight({ item, metricLabel, metricValue }) {
  return (
    <div className="bond-insight">
      <Link to={`/positions/${item.id}`}>{item.bond.name}</Link>
      <span>{item.bond.isin}</span>

      <div className="bond-insight-metric">
        <span>{metricLabel}</span>
        <strong>{metricValue}</strong>
      </div>
    </div>
  );
}

export default DashboardPage;