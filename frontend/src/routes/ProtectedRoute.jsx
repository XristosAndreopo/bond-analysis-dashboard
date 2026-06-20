/**
 * Protected route wrapper.
 *
 * If the user has no access token, they are redirected to the login page.
 */

import { Navigate } from "react-router-dom";

import { isAuthenticated } from "../auth/authService";

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;