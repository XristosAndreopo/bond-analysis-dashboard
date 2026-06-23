/**
 * Signup page.
 *
 * Creates a new inactive user account and redirects the user to the email
 * verification page.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signupUser } from "../api/authApi";

const INITIAL_FORM_DATA = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  password: "",
  password_confirm: "",
};

function SignupPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState(INITIAL_FORM_DATA);
  const [errorMessage, setErrorMessage] = useState("");
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
    setIsSubmitting(true);

    try {
      const response = await signupUser(formData);

      navigate("/verify-email", {
        state: {
          email: response.email || formData.email,
          detail: response.detail,
        },
      });
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
          <span className="auth-hero-pill">Create your workspace</span>
          <h2>Start tracking bonds with structured analysis.</h2>
          <p>
            Δημιούργησε λογαριασμό για να αποθηκεύεις Portfolio, Watchlist και
            AI-researched candidate bonds. Μετά το signup θα λάβεις κωδικό
            επιβεβαίωσης στο email σου.
          </p>
        </div>
      </section>

      <section className="auth-form-panel">
        <form className="auth-card auth-card-wide" onSubmit={handleSubmit}>
          <div className="auth-card-header">
            <span className="auth-kicker">New account</span>
            <h1>Create account</h1>
            <p>Συμπλήρωσε τα στοιχεία σου για να ξεκινήσεις.</p>
          </div>

          {errorMessage && <div className="error-box">{errorMessage}</div>}

          <div className="auth-two-column-grid">
            <label>
              First name
              <input
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                autoComplete="given-name"
                placeholder="First name"
              />
            </label>

            <label>
              Last name
              <input
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                autoComplete="family-name"
                placeholder="Last name"
              />
            </label>
          </div>

          <label>
            Username
            <input
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              autoComplete="username"
              placeholder="Choose a username"
              required
            />
          </label>

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

          <div className="auth-two-column-grid">
            <label>
              Password
              <input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                autoComplete="new-password"
                placeholder="Strong password"
                required
              />
            </label>

            <label>
              Confirm password
              <input
                name="password_confirm"
                type="password"
                value={formData.password_confirm}
                onChange={handleChange}
                autoComplete="new-password"
                placeholder="Repeat password"
                required
              />
            </label>
          </div>

          <p className="auth-helper-text">
            Χρησιμοποίησε δυνατό password με γράμματα, αριθμούς και σύμβολα.
          </p>

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>

          <p className="auth-switch-text">
            Έχεις ήδη λογαριασμό; <Link to="/login">Log in</Link>
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
    return "Δεν ήταν δυνατή η δημιουργία λογαριασμού.";
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
    return "Δεν ήταν δυνατή η δημιουργία λογαριασμού.";
  }

  return messages.join(" ");
}

export default SignupPage;
