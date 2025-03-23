import React from "react";
import { BrandButton } from "#/components/features/settings/brand-button";
import axios from "axios";
import { openHands, removeAuthTokenHeader, removeGitHubTokenHeader } from "#/api/open-hands-axios";

// Create a new axios instance just for the logout page
// This ensures we don't share any interceptors or auth state
const logoutPageAxios = axios.create();

export default function LogoutPage() {
  const [isLoading, setIsLoading] = React.useState(true);

  // Clear any auth state when the page loads
  React.useEffect(() => {
    const clearAuth = async () => {
      try {
        // Clear auth headers from both axios instances
        removeAuthTokenHeader();
        removeGitHubTokenHeader();
        
        // Clear any local storage items that might trigger re-auth
        localStorage.removeItem("openhands_last_page");
        
        setIsLoading(false);
      } catch (error) {
        console.error("Error clearing auth state:", error);
        setIsLoading(false);
      }
    };
    clearAuth();
  }, []);

  const handleLogin = () => {
    // For OSS mode or if no config is available, just go to home page
    window.location.href = "/";
  };

  if (isLoading) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6 bg-base">
      <h1 className="text-2xl font-semibold">
        You've been logged out
      </h1>
      <p className="text-base text-[#A3A3A3]">
        Thanks for using OpenHands. Click below to log back in.
      </p>
      <BrandButton
        testId="login-button"
        type="button"
        variant="primary"
        onClick={handleLogin}
      >
        Log In
      </BrandButton>
    </div>
  );
}