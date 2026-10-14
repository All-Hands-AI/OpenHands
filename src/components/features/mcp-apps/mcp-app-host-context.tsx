import React from "react";
import type { MCPAppArtifacts, MCPAppHost, MCPAppScope } from "#/types/mcp-app";

const EMPTY_ARTIFACTS: MCPAppArtifacts = new Map();

interface MCPAppHostContextValue {
  host: MCPAppHost | null;
  scope: MCPAppScope | null;
  artifacts: MCPAppArtifacts;
}

const MCPAppHostContext = React.createContext<MCPAppHostContextValue>({
  host: null,
  scope: null,
  artifacts: EMPTY_ARTIFACTS,
});

export interface MCPAppHostProviderProps {
  host: MCPAppHost | null;
  scope: MCPAppScope | null;
  artifacts?: MCPAppArtifacts;
  children: React.ReactNode;
}

// @spec MCA-004 — Shared and embedded views receive an explicit host and scope
export function MCPAppHostProvider({
  host,
  scope,
  artifacts = EMPTY_ARTIFACTS,
  children,
}: MCPAppHostProviderProps) {
  const value = React.useMemo(
    () => ({ host, scope, artifacts }),
    [host, scope, artifacts],
  );
  return (
    <MCPAppHostContext.Provider value={value}>
      {children}
    </MCPAppHostContext.Provider>
  );
}

export function useMCPAppHost(): MCPAppHostContextValue {
  return React.useContext(MCPAppHostContext);
}
