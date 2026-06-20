/**
 * Dashboard page.
 *
 * Shows a quick overview of the user's Portfolio bonds, including:
 * - portfolio summary
 * - signal distribution
 * - risk distribution
 * - top risk bond
 * - best value bond based on IV vs Market Price
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchDashboard } from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import { formatDecimal, formatMoney, formatPercent } from "../utils/formatters";

function DashboardPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await fetchDashboard();
        setDashboardData(data);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση του Dashboard.");
      }
    }

    loadDashboard();
  }, []);

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