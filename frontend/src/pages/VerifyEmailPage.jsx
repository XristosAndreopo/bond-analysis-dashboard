/**
 * Verify email page.
 *
 * Users enter the temporary code they received by email after signup.
 */

import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { resendVerificationCode, verifyEmail } from "../api/authApi";

function VerifyEmailPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: location.state?.email || "",
    code: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState(
    location.state?.detail || ""
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);

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
      const response = await verifyEmail(formData.email, formData.code);

      setSuccessMessage(
        response.detail || "Email verified successfully. You can now login."
      );

      setTimeout(() => {
        navigate("/login");
      }, 1000);
    } catch (error) {
      setErrorMessage(
        error?.response?.data?.detail ||
          "Δεν ήταν δυνατή η επιβεβαίωση του email."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleResendCode() {
    setErrorMessage("");
    setSuccessMessage("");
    setIsResending(true);

    try {
      const response = await resendVerificationCode(formData.email);

      setSuccessMessage(
        response.detail || "If an account exists, a new code will be sent."
      );
    } catch (error) {
      setErrorMessage("Δεν ήταν δυνατή η αποστολή νέου κωδικού.");
    } finally {
      setIsResending(false);
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
          <span className="auth-hero-pill">Email verification</span>
          <h2>Verify your account before login.</h2>
          <p>
            Πληκτρολόγησε τον 6ψήφιο κωδικό που στάλθηκε στο email σου. Στο
            development περιβάλλον, αν χρησιμοποιείς console email backend, ο
            κωδικός εμφανίζεται στο terminal του Django server.
          </p>
        </div>
      </section>

      <section className="auth-form-panel">
        <form className="auth-card" onSubmit={handleSubmit}>
          <div className="auth-card-header">
            <span className="auth-kicker">Verify email</span>
            <h1>Enter verification code</h1>
            <p>Ο λογαριασμός ενεργοποιείται μόνο μετά την επιβεβαίωση.</p>
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
            Verification code
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

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Verifying..." : "Verify email"}
          </button>

          <button
            className="auth-secondary-button"
            type="button"
            disabled={isResending || !formData.email}
            onClick={handleResendCode}
          >
            {isResending ? "Sending..." : "Resend code"}
          </button>

          <p className="auth-switch-text">
            Έχεις ήδη επιβεβαιώσει email; <Link to="/login">Back to login</Link>
          </p>
        </form>
      </section>
    </main>
  );
}

export default VerifyEmailPage;
