/**
 * Application layout.
 *
 * This layout wraps all authenticated pages.
 *
 * It contains:
 * - the left vertical Sidebar
 * - the main content area where child routes are rendered
 *
 * Important:
 *   The <Outlet /> component is required by React Router.
 *   Without it, the sidebar appears but the selected page content remains blank.
 */

import { Outlet } from "react-router-dom";

import Sidebar from "../components/Sidebar";

function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default AppLayout;