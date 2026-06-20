/**
 * Signal badge component.
 *
 * Displays the final analytical signal as a user-friendly badge. The signal is
 * educational/analytical and must not be presented as investment advice.
 */

function SignalBadge({ signal, label }) {
  const normalizedSignal = signal || "REVIEW";

  return (
    <span className={`badge signal-badge signal-${normalizedSignal}`}>
      {label || "Επανεξέταση"}
    </span>
  );
}

export default SignalBadge;