import React from "react";
import { useAuth } from "../context/auth-context-updated";

interface PrivateRouteProps {
  children: React.ReactNode;
}

function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    // Show loading spinner while checking authentication
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login if not authenticated
    window.location.href = "/login";
    return null;
  }

  return children;
}

export default PrivateRoute;
