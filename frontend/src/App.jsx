/**
 * Main application router.
 *
 * Public pages:
 * - Dashboard preview
 * - Login
 * - Signup
 * - Forgot password
 *
 * Protected pages:
 * - Portfolio
 * - Watchlist
 * - Discover Bonds
 * - FX Rates
 * - Position pages
 */

import { Navigate, Route, Routes } from "react-router-dom";

import { isAuthenticated } from "./auth/authService";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./routes/ProtectedRoute";
import AddPositionPage from "./pages/AddPositionPage";
import BondDetailPage from "./pages/BondDetailPage";
import DashboardPage from "./pages/DashboardPage";
import DiscoverBondsPage from "./pages/DiscoverBondsPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import FXRatesPage from "./pages/FXRatesPage";
import LoginPage from "./pages/LoginPage";
import PortfolioPage from "./pages/PortfolioPage";
import SignupPage from "./pages/SignupPage";
import WatchlistPage from "./pages/WatchlistPage";

/**
 * Render Dashboard differently depending on authentication state.
 *
 * - Logged-in user: Dashboard inside the authenticated AppLayout with Sidebar.
 * - Guest user: Public Dashboard preview without private data.
 */
function DashboardRoute() {
  if (isAuthenticated()) {
    return (
      <ProtectedRoute>
        <AppLayout>
          <DashboardPage />
        </AppLayout>
      </ProtectedRoute>
    );
  }

  return <DashboardPage />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/dashboard" element={<DashboardRoute />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="watchlist" element={<WatchlistPage />} />
        <Route path="discover-bonds" element={<DiscoverBondsPage />} />
        <Route path="fx-rates" element={<FXRatesPage />} />
        <Route path="positions/new" element={<AddPositionPage />} />
        <Route path="positions/:positionId" element={<BondDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;