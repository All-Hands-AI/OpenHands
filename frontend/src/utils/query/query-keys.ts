/**
 * This file contains all the query keys used in the application.
 * It helps maintain consistency and avoid typos in query keys.
 */

export const QueryKeys = {
  // Configuration
  config: ["config"] as const,
  aiConfigOptions: ["ai-config-options"] as const,

  // User
  user: ["user"] as const,
  isAuthed: ["is-authed"] as const,
  githubUser: ["github-user"] as const,
  balance: ["balance"] as const,
  settings: ["settings"] as const,

  // Conversations
  conversations: ["conversations"] as const,
  conversation: (id: string) => ["conversation", id] as const,
  conversationConfig: (id: string) => ["conversation-config", id] as const,

  // Files
  files: (conversationId: string, path?: string) =>
    ["files", conversationId, path] as const,
  file: (conversationId: string, path: string) =>
    ["file", conversationId, path] as const,

  // GitHub
  githubInstallations: ["github-installations"] as const,
  githubRepositories: (query: string) =>
    ["github-repositories", query] as const,

  // Runtime
  activeHost: ["active-host"] as const,
  vscodeUrl: (conversationId: string) =>
    ["vscode-url", conversationId] as const,

  // Traces
  traces: (conversationId: string) => ["traces", conversationId] as const,

  // Security
  riskSeverity: (conversationId: string, command: string) =>
    ["risk-severity", conversationId, command] as const,
  policy: ["policy"] as const,
};
