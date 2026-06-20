/**
 * Sidebar navigation.
 *
 * The application uses a vertical left sidebar.
 *
 * Main navigation:
 * - Dashboard
 * - Portfolio
 * - My Watchlist
 * - Discover Bonds
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
            <span>My Watchlist</span>
          </NavLink>

          <NavLink to="/discover-bonds">
            <span className="nav-icon">🔎</span>
            <span>Discover Bonds</span>
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
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.25.8-.55v-2.1c-3.2.7-3.9-1.55-3.9-1.55-.55-1.35-1.3-1.7-1.3-1.7-1.05-.7.1-.7.1-.7 1.15.1 1.75 1.2 1.75 1.2 1.05 1.75 2.7 1.25 3.35.95.1-.75.4-1.25.75-1.55-2.55-.3-5.25-1.3-5.25-5.7 0-1.25.45-2.3 1.2-3.1-.1-.3-.5-1.55.1-3.05 0 0 1-.3 3.2 1.2.95-.25 1.9-.4 2.9-.4s1.95.15 2.9.4c2.2-1.5 3.2-1.2 3.2-1.2.6 1.5.2 2.75.1 3.05.75.8 1.2 1.85 1.2 3.1 0 4.4-2.7 5.4-5.25 5.7.4.35.8 1.05.8 2.1v3.1c0 .3.2.65.8.55A11.52 11.52 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S.02 4.88.02 3.5 1.14 1 2.5 1s2.48 1.12 2.48 2.5ZM.4 8h4.2v14H.4V8Zm7.2 0h4v1.9h.05c.55-1.05 1.95-2.15 4-2.15 4.3 0 5.1 2.85 5.1 6.55V22h-4.2v-6.8c0-1.6-.05-3.7-2.25-3.7-2.25 0-2.6 1.75-2.6 3.6V22H7.6V8Z" />
    </svg>
  );
}

export default Sidebar;