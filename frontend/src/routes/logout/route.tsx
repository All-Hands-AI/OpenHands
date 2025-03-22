import React from "react";
import { BrandButton } from "#/components/features/settings/brand-button";

export default function LogoutPage() {

  const handleLogin = () => {
    // Use the stored config from window.__OPENHANDS_CONFIG__ or default to GitHub auth URL
    const config = window.__OPENHANDS_CONFIG__;
    if (config?.APP_MODE === "saas" && config?.GITHUB_CLIENT_ID) {
      const url = new URL(window.location.href);
      url.searchParams.set("redirect_uri", window.location.origin);
      url.searchParams.set("client_id", config.GITHUB_CLIENT_ID);
      window.location.href = `https://github.com/login/oauth/authorize?${url.searchParams.toString()}`;
    } else {
      // For OSS mode or if no config is available, just go to home page
      window.location.href = "/";
    }
  };

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