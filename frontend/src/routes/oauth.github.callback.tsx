import { useNavigate, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "#/hooks/query/use-config";

function OAuthGitHubCallback() {
  const navigate = useNavigate();
  const { data: config } = useConfig();
  const [searchParams] = useSearchParams();
  const { setGitHubToken } = useAuth();

  const code = searchParams.get("code");

  const { data, isSuccess, error } = useQuery({
    queryKey: ["access_token", code],
    queryFn: () => OpenHands.getGitHubAccessToken(code!),
    enabled: !!code,
  });

  React.useEffect(() => {
    if (isSuccess) {
      setGitHubToken(data.access_token);
      navigate("/");
      if (config?.APP_SLUG)
        window.open(
          `https://github.com/apps/${config.APP_SLUG}/installations/new`,
          "_blank",
        );
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
