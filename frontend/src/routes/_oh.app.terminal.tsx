import React from "react";
import Terminal from "#/components/features/terminal/terminal";

function TerminalPage() {
  const secrets = React.useMemo(
    // secrets to filter go here
    () => [].filter((secret) => secret !== null),
    [],
  );
  return <Terminal secrets={secrets} />;
}

export default TerminalPage;
