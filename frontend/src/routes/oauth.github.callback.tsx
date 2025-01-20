import { useNavigate, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

function OAuthGitHubCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setAccessTokens, setUserId } = useAuth();

  const code = searchParams.get("code");
  const requesterUrl = new URL(window.location.href)
  const redirectUrl = `${requesterUrl.origin}/oauth/github/callback`

  const { data, isSuccess, error } = useQuery({
    queryKey: ["access_token", code],
    queryFn: () => OpenHands.getGitHubAccessToken(code!, redirectUrl),
    enabled: !!code,
  });

  console.debug(`data: ${JSON.stringify(data)}, isSuccess: ${isSuccess}`)

  React.useEffect(() => {
    if (isSuccess) {
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
