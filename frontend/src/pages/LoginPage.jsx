/**
 * Login page.
 *
 * Users authenticate with username and password. On success, JWT tokens are
 * stored and the user is redirected to the dashboard.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getCurrentUser, loginUser } from "../api/authApi";
import { setStoredUser, storeTokens } from "../auth/authService";

function LoginPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });

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
      const tokens = await loginUser(formData.username, formData.password);

      storeTokens(tokens);

      try {
        const currentUser = await getCurrentUser();
        setStoredUser(currentUser);
      } catch (userError) {
        // Login should not fail only because user profile loading failed.
      }

      navigate("/dashboard");
    } catch (error) {
      setErrorMessage(
        "Δεν ήταν δυνατή η σύνδεση. Έλεγξε username και password."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthPageShell>
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-card-header">
          <span className="auth-kicker">Welcome back</span>
          <h1>Log in</h1>
          <p>Συνδέσου για να δεις το Portfolio, το Watchlist και τα bond signals σου.</p>
        </div>

        {errorMessage && <div className="error-box">{errorMessage}</div>}

        <label>
          Username
          <input
            name="username"
            type="text"
            value={formData.username}
            onChange={handleChange}
            autoComplete="username"
            placeholder="Enter your username"
            required
          />
        </label>

        <label>
          Password
          <input
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            autoComplete="current-password"
            placeholder="Enter your password"
            required
          />
        </label>

        <div className="auth-form-row">
          <Link to="/forgot-password">Forgot password?</Link>
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Log in"}
        </button>

        <p className="auth-switch-text">
          Δεν έχεις λογαριασμό; <Link to="/signup">Create account</Link>
        </p>
      </form>
    </AuthPageShell>
  );
}

function AuthPageShell({ children }) {
  return (
    <main className="auth-page">
      <section className="auth-hero-panel">
        <Link className="auth-logo-link" to="/dashboard">
          <span className="auth-logo-mark">B</span>
          <span>Bond Analysis Dashboard</span>
        </Link>

        <div className="auth-hero-content">
          <span className="auth-hero-pill">AI-powered bond research</span>
          <h2>Analyze bonds. Track risk. Build a smarter watchlist.</h2>
          <p>
            Παρακολούθησε ομόλογα, αξιολόγησε ρίσκο, κράτησε watchlist και
            χρησιμοποίησε AI research με ελεγχόμενη πηγή δεδομένων.
          </p>
        </div>

        <div className="auth-feature-grid">
          <div>
            <strong>Portfolio</strong>
            <span>Risk and signal overview</span>
          </div>
          <div>
            <strong>Watchlist</strong>
            <span>Candidate bonds to review</span>
          </div>
          <div>
            <strong>AI Discovery</strong>
            <span>Structured bond research</span>
          </div>
        </div>
      </section>

      <section className="auth-form-panel">{children}</section>
    </main>
  );
}

export default LoginPage;