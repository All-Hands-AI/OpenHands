import React from "react";
import { useAuth } from "#/context/auth-context";

function TerminalRoute() {
  const { gitHubToken } = useAuth();
  const secrets = React.useMemo(
    () => [gitHubToken].filter((secret) => secret !== null),
    [gitHubToken],
  );

  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  return (
    <React.Suspense fallback={<div className="h-full" />}>
      <Terminal secrets={secrets} />
    </React.Suspense>
  );
}

export default TerminalRoute;
