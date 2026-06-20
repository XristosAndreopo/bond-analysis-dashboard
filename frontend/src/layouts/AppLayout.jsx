/**
 * Main application layout.
 *
 * This layout provides the vertical left sidebar and a content area.
 */

import Sidebar from "../components/Sidebar";

function AppLayout({ children, currentUser, onLogout }) {
  return (
    <div className="app-shell">
      <Sidebar currentUser={currentUser} onLogout={onLogout} />

      <main className="main-content">{children}</main>
    </div>
  );
}

export default AppLayout;