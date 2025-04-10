import React from "react";

function TerminalTab() {
  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  // Define empty secrets array for filtering
  const secrets = React.useMemo(
    // secrets to filter go here
    () => [].filter((secret) => secret !== null),
    [],
  );

  return (
    <div className="h-full flex flex-col">
      <div className="flex-grow overflow-auto">
        {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
         * that it loads only in the client-side. */}
        <React.Suspense fallback={<div className="h-full" />}>
          <Terminal secrets={secrets} />
        </React.Suspense>
      </div>
    </div>
  );
}

export default TerminalTab;
