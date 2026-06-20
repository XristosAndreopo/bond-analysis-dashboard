/**
 * Sidebar navigation.
 *
 * The application uses a vertical left sidebar.
 *
 * Main navigation:
 * - Dashboard
 * - Portfolio
 * - Watchlist
 * - FX Rates
 *
 * Footer:
 * - Logged-in user
 * - Logout button
 * - Contact links with visual icons
 */

import { NavLink, useNavigate } from "react-router-dom";

import { clearTokens, getStoredUser } from "../auth/authService";

function Sidebar() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function handleLogout() {
    clearTokens();
    navigate("/login");
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-main">
        <div className="sidebar-brand">
          <span className="sidebar-logo">BA</span>

          <div className="sidebar-brand-text">
            <strong>Bond Analysis</strong>
            <small>Dashboard</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard">
            <span className="nav-icon">📊</span>
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/portfolio">
            <span className="nav-icon">💼</span>
            <span>Portfolio</span>
          </NavLink>

          <NavLink to="/watchlist">
            <span className="nav-icon">👁️</span>
            <span>Watchlist</span>
          </NavLink>

          <NavLink to="/fx-rates">
            <span className="nav-icon">💱</span>
            <span>FX Rates</span>
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span>Signed in as</span>
          <strong>{user?.username || "User"}</strong>
        </div>

        <button type="button" className="logout-button" onClick={handleLogout}>
          Log out
        </button>

        <div className="contact-block">
          <strong>Contact Us</strong>

          <div className="contact-icons">
            <a href="mailto:contact@example.com" aria-label="Email">
              <MailIcon />
            </a>

            <a
              href="https://github.com/XristosAndreopo"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub"
            >
              <GitHubIcon />
            </a>

            <a
              href="https://www.linkedin.com"
              target="_blank"
              rel="noreferrer"
              aria-label="LinkedIn"
            >
              <LinkedInIcon />
            </a>
          </div>
        </div>
      </div>
    </aside>
  );
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 5h16c1.1 0 2 .9 2 2v10c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V7c0-1.1.9-2 2-2Zm0 3.2v8.8h16V8.2l-8 5.2-8-5.2Zm1.4-1.2L12 11.3 18.6 7H5.4Z" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 .5C5.7.5.6 5.6.6 11.9c0 5 3.3 9.3 7.9 10.8.6.1.8-.3.8-.6v-2.1c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 .1.7 2.1 2.8 1.5.1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.6.1-3.2 0 0 1-.3 3.3 1.2 1-.3 2-.4 3-.4s2 .1 3 .4c2.3-1.5 3.3-1.2 3.3-1.2.6 1.6.2 2.9.1 3.2.8.9 1.2 1.9 1.2 3.2 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.8C23.4 5.6 18.3.5 12 .5Z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4.98 3.5C4.98 4.9 3.9 6 2.5 6S0 4.9 0 3.5 1.1 1 2.5 1 4.98 2.1 4.98 3.5ZM.3 8.1h4.4V23H.3V8.1Zm7.1 0h4.2v2h.1c.6-1.1 2-2.3 4.1-2.3 4.4 0 5.2 2.9 5.2 6.6V23h-4.4v-7.6c0-1.8 0-4.1-2.5-4.1s-2.9 2-2.9 4V23H7.4V8.1Z" />
    </svg>
  );
}

export default Sidebar;