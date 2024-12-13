import React from "react";
import { useAuth } from "#/context/auth-context";

function TerminalRoute() {
  const { token, gitHubToken } = useAuth();
  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  const secrets = React.useMemo(
    () => [gitHubToken, token].filter((secret) => secret !== null),
    [gitHubToken, token],
  );

  return (
    <React.Suspense fallback={<div className="h-full" />}>
      <Terminal secrets={secrets} />
    </React.Suspense>
  );
}

export default TerminalRoute;