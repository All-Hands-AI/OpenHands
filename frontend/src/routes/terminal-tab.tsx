import React from "react";

function TerminalTab() {
  const Terminal = React.useMemo(
    () => React.lazy(() => import("#/components/features/terminal/terminal")),
    [],
  );

  return (
    <div className="h-full flex flex-col">
      <div className="flex-grow overflow-auto">
        {/* Terminal uses some API that is not compatible in a server-environment. For this reason, we lazy load it to ensure
         * that it loads only in the client-side. */}
        <React.Suspense fallback={<div className="h-full" />}>
          <Terminal />
        </React.Suspense>
      </div>
    </div>
  );
}

export default TerminalTab;
