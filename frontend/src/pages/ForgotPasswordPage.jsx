/**
 * Forgot password page.
 *
 * The user submits an email and receives a temporary reset code. The response
 * remains generic so the app does not reveal whether the email exists.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { requestPasswordReset } from "../api/authApi";

function ForgotPasswordPage() {
  const navigate = useNavigate();

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

      setTimeout(() => {
        navigate("/reset-password", {
          state: {
            email,
          },
        });
      }, 800);
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
            Θα λάβεις προσωρινό 6ψήφιο κωδικό. Για λόγους ασφαλείας, η
            εφαρμογή δεν αποκαλύπτει αν υπάρχει ή όχι λογαριασμός με το email.
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
            {isSubmitting ? "Sending..." : "Send reset code"}
          </button>

          <p className="auth-switch-text">
            Έχεις ήδη κωδικό; <Link to="/reset-password">Reset password</Link>
          </p>

          <p className="auth-switch-text">
            Θυμήθηκες τον κωδικό; <Link to="/login">Back to login</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

export default ForgotPasswordPage;
