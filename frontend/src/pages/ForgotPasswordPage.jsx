/**
 * Forgot password page.
 *
 * MVP behavior:
 * - user submits an email
 * - backend returns a generic safe response
 * - real email reset flow can be added later
 */

import { useState } from "react";
import { Link } from "react-router-dom";

import { requestPasswordReset } from "../api/authApi";

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setErrorMessage("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const response = await requestPasswordReset(email);

      setSuccessMessage(
        response.detail ||
          "If an account exists, password reset instructions will be sent."
      );
    } catch (error) {
      setErrorMessage("Δεν ήταν δυνατή η αποστολή αιτήματος επαναφοράς.");
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
          <span className="auth-hero-pill">Account recovery</span>
          <h2>Reset access safely.</h2>
          <p>
            Για λόγους ασφαλείας, η εφαρμογή δεν αποκαλύπτει αν υπάρχει ή όχι
            λογαριασμός με το email που θα δώσεις.
          </p>
        </div>
      </section>

      <section className="auth-form-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <div className="auth-card-header">
            <span className="auth-kicker">Forgot password</span>
            <h1>Password reset</h1>
            <p>Πληκτρολόγησε το email του λογαριασμού σου.</p>
          </div>

          {errorMessage && <div className="error-box">{errorMessage}</div>}
          {successMessage && <div className="success-box">{successMessage}</div>}

          <label>
            Email
            <input
              name="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </label>

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Sending..." : "Send reset instructions"}
          </button>

          <p className="auth-switch-text">
            Θυμήθηκες τον κωδικό; <Link to="/login">Back to login</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

export default ForgotPasswordPage;