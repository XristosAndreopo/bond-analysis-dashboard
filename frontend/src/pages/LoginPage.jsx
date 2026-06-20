/**
 * Login page.
 *
 * Users authenticate with username and password. On success, JWT tokens are
 * stored and the user is redirected to the dashboard.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginUser } from "../api/authApi";
import { storeTokens } from "../auth/authService";

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
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Bond Analysis Dashboard</h1>
        <p>Σύνδεση χρήστη</p>

        {errorMessage && <div className="error-box">{errorMessage}</div>}

        <label>
          Username
          <input
            name="username"
            type="text"
            value={formData.username}
            onChange={handleChange}
            autoComplete="username"
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
            required
          />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Log in"}
        </button>
      </form>
    </div>
  );
}

export default LoginPage;