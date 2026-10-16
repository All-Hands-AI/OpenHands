import type { AgentKind } from "@openhands/typescript-client";
import type { AgentProfileSummary } from "#/api/agent-profiles-service/agent-profiles-service.api";
import { useAgentProfiles } from "#/hooks/query/use-agent-profiles";
import { useSettings } from "#/hooks/query/use-settings";

/**
 * The agent profile the user has activated — the authoritative "current agent"
 * now that Settings → Agent IS the profile library (#1571). `activate` is
 * pointer-only and never writes `settings.agent_settings`, so the active
 * profile — not the global agent settings — is the source of truth for what
 * kind of agent (OpenHands vs ACP) is in effect.
 *
 * Cached profile data survives a failed refetch; `isError` is set only when a
 * failed fetch left nothing to decide from, and `agentKind` is then
 * `undefined`. Without an active profile `agentKind` comes from the global
 * agent settings: briefly while the list loads, and for good when no profile
 * is active, the one case a launch sends them.
 */
export function useActiveAgentProfile(): {
  activeProfile: AgentProfileSummary | null;
  agentKind: AgentKind | undefined;
  isLoading: boolean;
  isError: boolean;
} {
  const { data, isLoading, isError: queryError } = useAgentProfiles();
  const { data: settings } = useSettings();
  const activeId = data?.active_agent_profile_id ?? null;
  const activeProfile =
    data?.profiles?.find((p) => p.id != null && p.id === activeId) ?? null;
  const isError = queryError && !data;
  const settingsKind = settings?.agent_settings?.agent_kind;
  let agentKind: AgentKind | undefined;
  if (activeProfile) agentKind = activeProfile.agent_kind;
  else if (!isError && (settingsKind === "acp" || settingsKind === "openhands"))
    agentKind = settingsKind;
  return { activeProfile, agentKind, isLoading, isError };
}

export function useActiveAgentKind(): AgentKind | undefined {
  return useActiveAgentProfile().agentKind;
}
