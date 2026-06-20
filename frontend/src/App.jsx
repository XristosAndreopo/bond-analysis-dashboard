/**
 * Main application component.
 *
 * Defines the frontend routes and controls the authenticated user state.
 */

import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { getCurrentUser } from "./api/authApi";
import { clearTokens, isAuthenticated } from "./auth/authService";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./routes/ProtectedRoute";

import AddPositionPage from "./pages/AddPositionPage";
import BondDetailPage from "./pages/BondDetailPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PortfolioPage from "./pages/PortfolioPage";
import WatchlistPage from "./pages/WatchlistPage";

function App() {
  const navigate = useNavigate();

  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    async function loadCurrentUser() {
      if (!isAuthenticated()) {
        return;
      }

      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
      } catch (error) {
        clearTokens();
        navigate("/login");
      }
    }

    loadCurrentUser();
  }, [navigate]);

  function handleLogout() {
    clearTokens();
    setCurrentUser(null);
    navigate("/login");
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          isAuthenticated() ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout currentUser={currentUser} onLogout={handleLogout}>
              <DashboardPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/portfolio"
        element={
          <ProtectedRoute>
            <AppLayout currentUser={currentUser} onLogout={handleLogout}>
              <PortfolioPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/watchlist"
        element={
          <ProtectedRoute>
            <AppLayout currentUser={currentUser} onLogout={handleLogout}>
              <WatchlistPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/positions/new"
        element={
          <ProtectedRoute>
            <AppLayout currentUser={currentUser} onLogout={handleLogout}>
              <AddPositionPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/positions/:id"
        element={
          <ProtectedRoute>
            <AppLayout currentUser={currentUser} onLogout={handleLogout}>
              <BondDetailPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;