/**
 * Query keys for React Query
 * This file defines the query keys used throughout the application
 */

export const QueryKeys = {
  // Agent state
  agent: ["agent"],

  // Browser state
  browser: ["browser"],

  // Chat messages
  chat: ["chat"],

  // Code state
  code: ["code"],

  // Command state
  command: ["command"],

  // File state
  fileState: ["fileState"],

  // Initial query
  initialQuery: ["initialQuery"],

  // Jupyter state
  jupyter: ["jupyter"],

  // Security analyzer
  securityAnalyzer: ["securityAnalyzer"],

  // Status message
  status: ["status"],

  // Metrics
  metrics: ["metrics"],

  // Config
  config: ["config"],

  // Files
  files: (path: string) => ["files", path],
};
