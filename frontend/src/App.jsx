/**
 * Main application router.
 *
 * Defines all frontend routes and protects authenticated pages.
 */

import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./routes/ProtectedRoute";
import AddPositionPage from "./pages/AddPositionPage";
import BondDetailPage from "./pages/BondDetailPage";
import DashboardPage from "./pages/DashboardPage";
import FXRatesPage from "./pages/FXRatesPage";
import LoginPage from "./pages/LoginPage";
import PortfolioPage from "./pages/PortfolioPage";
import WatchlistPage from "./pages/WatchlistPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="watchlist" element={<WatchlistPage />} />
        <Route path="fx-rates" element={<FXRatesPage />} />
        <Route path="positions/new" element={<AddPositionPage />} />
        <Route path="positions/:positionId" element={<BondDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;