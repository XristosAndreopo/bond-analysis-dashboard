/**
 * Risk badge component.
 *
 * Displays the calculated risk level using a visual badge. The component
 * remains independent from the backend labels and safely handles missing data.
 */

function RiskBadge({ riskLevel, label }) {
  const normalizedRiskLevel = riskLevel || "UNKNOWN";

  return (
    <span className={`badge risk-badge risk-${normalizedRiskLevel}`}>
      {label || "-"}
    </span>
  );
}

export default RiskBadge;