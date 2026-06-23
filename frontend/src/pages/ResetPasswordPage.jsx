/**
 * Reset password page.
 *
 * Users submit:
 * - email
 * - temporary reset code
 * - new password
 * - new password confirmation
 */

import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { resetPassword } from "../api/authApi";

function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: location.state?.email || "",
    code: "",
    new_password: "",
    new_password_confirm: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setErrorMessage("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const response = await resetPassword(formData);

      setSuccessMessage(
        response.detail || "Password reset successfully. You can now login."
      );

      setTimeout(() => {
        navigate("/login");
      }, 1000);
    } catch (error) {
      setErrorMessage(buildApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-hero-panel">
        <Link className="auth-logo-link" to="/dashboard">
          <span className="auth-logo-mark">B</span>
          <span>Bond Analysis Dashboard</span>
        </Link>

        <div className="auth-hero-content">
          <span className="auth-hero-pill">New password</span>
          <h2>Use your temporary code to set a new password.</h2>
          <p>
            Συμπλήρωσε τον κωδικό που έλαβες, τον νέο κωδικό πρόσβασης και την
            επιβεβαίωσή του.
          </p>
        </div>
      </section>

      <section className="auth-form-panel">
        <form className="auth-card auth-card-wide" onSubmit={handleSubmit}>
          <div className="auth-card-header">
            <span className="auth-kicker">Reset password</span>
            <h1>Set new password</h1>
            <p>Ο προσωρινός κωδικός ισχύει για λίγα λεπτά.</p>
          </div>

          {errorMessage && <div className="error-box">{errorMessage}</div>}
          {successMessage && <div className="success-box">{successMessage}</div>}

          <label>
            Email
            <input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </label>

          <label>
            Temporary code
            <input
              className="auth-code-input"
              name="code"
              type="text"
              inputMode="numeric"
              maxLength="6"
              value={formData.code}
              onChange={handleChange}
              placeholder="000000"
              required
            />
          </label>

          <div className="auth-two-column-grid">
            <label>
              New password
              <input
                name="new_password"
                type="password"
                value={formData.new_password}
                onChange={handleChange}
                autoComplete="new-password"
                placeholder="New password"
                required
              />
            </label>

            <label>
              Confirm new password
              <input
                name="new_password_confirm"
                type="password"
                value={formData.new_password_confirm}
                onChange={handleChange}
                autoComplete="new-password"
                placeholder="Repeat new password"
                required
              />
            </label>
          </div>

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Resetting..." : "Reset password"}
          </button>

          <p className="auth-switch-text">
            Δεν έχεις κωδικό; <Link to="/forgot-password">Request reset code</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

/**
 * Convert a DRF validation error response into readable text.
 *
 * @param {object} error - Axios error.
 * @returns {string} Error message.
 */
function buildApiErrorMessage(error) {
  const data = error?.response?.data;

  if (!data) {
    return "Δεν ήταν δυνατή η αλλαγή κωδικού.";
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  const messages = [];

  Object.entries(data).forEach(([field, value]) => {
    if (Array.isArray(value)) {
      messages.push(`${field}: ${value.join(" ")}`);
    } else if (typeof value === "string") {
      messages.push(`${field}: ${value}`);
    } else if (value && typeof value === "object") {
      messages.push(`${field}: ${JSON.stringify(value)}`);
    }
  });

  if (messages.length === 0) {
    return "Δεν ήταν δυνατή η αλλαγή κωδικού.";
  }

  return messages.join(" ");
}

export default ResetPasswordPage;
