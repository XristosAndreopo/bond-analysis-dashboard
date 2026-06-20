/**
 * Vertical sidebar navigation.
 *
 * The sidebar is intentionally simple:
 * - Dashboard
 * - Portfolio
 * - Watchlist
 * - Current user
 * - Logout
 *
 * Social/contact links use placeholders so they can be replaced later.
 */

import { NavLink } from "react-router-dom";

function Sidebar({ currentUser, onLogout }) {
  const username = currentUser?.full_name || currentUser?.username || "User";

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <span className="brand-mark">B</span>
          <span className="brand-text">Bond Analysis</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className="sidebar-link">
            Dashboard
          </NavLink>

          <NavLink to="/portfolio" className="sidebar-link">
            Portfolio
          </NavLink>

          <NavLink to="/watchlist" className="sidebar-link">
            Watchlist
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-user">
          <span className="sidebar-user-label">Signed in as</span>
          <strong>{username}</strong>
        </div>

        <button type="button" className="logout-button" onClick={onLogout}>
          Log out
        </button>

        <a href="mailto:your-email@example.com" className="contact-button">
          Contact Us
        </a>

        <div className="social-links">
          <a href="mailto:your-email@example.com" aria-label="Email">
            ✉
          </a>

          <a
            href="https://github.com/your-github-profile"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
          >
            GH
          </a>

          <a
            href="https://www.linkedin.com/in/your-linkedin-profile"
            target="_blank"
            rel="noreferrer"
            aria-label="LinkedIn"
          >
            in
          </a>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;