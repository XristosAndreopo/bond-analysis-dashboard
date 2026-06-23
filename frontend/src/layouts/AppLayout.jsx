/**
 * Application layout.
 *
 * This layout wraps authenticated pages.
 *
 * It contains:
 * - the left vertical Sidebar
 * - the main content area
 *
 * The component supports two rendering modes:
 * - children mode: used when a route wants to render a specific page directly
 * - Outlet mode: used by nested React Router routes
 */

import { Outlet } from "react-router-dom";

import Sidebar from "../components/Sidebar";

function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        {children || <Outlet />}
      </main>
    </div>
  );
}

export default AppLayout;