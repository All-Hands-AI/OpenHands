import { useNavigate, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { SettingsUpToDateProvider } from "#/context/settings-up-to-date-context";

function OAuthGitHubCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setAccessTokens, setUserId } = useAuth();

  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const session_state = searchParams.get("session_state");
  const iss = searchParams.get("iss");
  const requesterUrl = new URL(window.location.href)
  const redirectUrl = `${requesterUrl.origin}/oauth/github/callback`
  console.log("code:", code, "\nstate:", state, "\nredirectUrl:", redirectUrl, "\nsession_state:", session_state, "\niss:", iss);

  const { data, isSuccess, error } = useQuery({
    queryKey: ["access_token", code],
    queryFn: () => OpenHands.getGitHubAccessToken(code!, redirectUrl),
    enabled: !!code,
  });

  React.useEffect(() => {
    if (isSuccess) {
      console.log("data:", data);
      setAccessTokens(data.providerAccessToken, data.keycloakAccessToken);
      setUserId(data.keycloakUserId)
      navigate("/");
    }
  }, [isSuccess]);

  if (error) {
    return (
      <div>
        <h1>Error</h1>
        <p>{error.message}</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Redirecting...</h1>
    </div>
  );
}

export default OAuthGitHubCallback;
