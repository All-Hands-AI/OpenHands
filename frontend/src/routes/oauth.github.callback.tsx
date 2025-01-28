import { useNavigate, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";

function OAuthGitHubCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const code = searchParams.get("code");

  const { isSuccess, error } = useQuery({
    queryKey: ["access_token", code],
    queryFn: () => OpenHands.getGitHubAccessToken(code!),
    enabled: !!code,
  });

  React.useEffect(() => {
    if (isSuccess) {
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
