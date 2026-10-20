import type { AgentProfile } from "#/api/agent-profiles-service/agent-profiles-service.api";

/** Lists a new profile takes from their global pages, and the LLM picker's pick. */
const NOT_COPIED_FROM_DEFAULT = [
  "llm_profile_ref",
  "public_skills",
  "disabled_skills",
  "mcp_server_refs",
  "secret_refs",
] as const;

/** The settings a new profile copies from an OpenHands `default`. */
export function newProfileSeed(
  defaultProfile: AgentProfile | null | undefined,
): AgentProfile | null {
  if (defaultProfile?.agent_kind !== "openhands") return null;
  const seed: Record<string, unknown> = { ...defaultProfile };
  NOT_COPIED_FROM_DEFAULT.forEach((key) => delete seed[key]);
  return seed as unknown as AgentProfile;
}
