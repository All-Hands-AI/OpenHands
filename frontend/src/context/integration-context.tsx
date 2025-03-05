import React from "react";

interface IntegrationContextType {
  hasGitHubConnected: boolean;
  setHasGitHubConnected: (value: boolean) => void;
}

const IntegrationContext = React.createContext<
  IntegrationContextType | undefined
>(undefined);

function IntegrationProvider({ children }: React.PropsWithChildren) {
  const [hasGitHubConnected, setHasGitHubConnected] = React.useState(false);

  const value = React.useMemo(
    () => ({ hasGitHubConnected, setHasGitHubConnected }),
    [hasGitHubConnected, setHasGitHubConnected],
  );

  return <IntegrationContext value={value}>{children}</IntegrationContext>;
}

function useIntegrations() {
  const context = React.useContext(IntegrationContext);
  if (context === undefined) {
    throw new Error(
      "useIntegrations must be used within a IntegrationProvider",
    );
  }
  return context;
}

export { IntegrationProvider, useIntegrations };
