import type { QueryClient } from "@tanstack/react-query";
import { HttpError } from "@openhands/typescript-client";
import AgentProfilesService, {
  WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME,
  type AgentProfile,
  type AgentProfileSaveInput,
} from "#/api/agent-profiles-service/agent-profiles-service.api";
import {
  getActiveBackend,
  isNoBackend,
} from "#/api/backend-registry/active-store";
import { mergeAgentProfileSaveInput } from "#/components/features/settings/agent-profiles/merge-agent-profile-save-input";
import { AGENT_PROFILES_QUERY_KEYS } from "#/hooks/query/query-keys";
import { settleRunningDefaultAgentProfileMigration } from "#/hooks/use-migrate-default-agent-profile";
import i18n from "#/i18n";
import { I18nKey } from "#/i18n/declaration";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import {
  buildSkillEnablementFilter,
  CATALOG_SKILL_NAMES,
  profileSkillEnablement,
  sameSkillSelection,
  toggleSkill,
  toProfileSkillFields,
  type SkillEnablement,
} from "#/utils/skill-enablement";

/** The fields to change on `default`, or `null` when it already matches. */
export type DefaultProfileChange = (
  profile: AgentProfile,
) => Partial<AgentProfileSaveInput> | null;

let queue: Promise<void> = Promise.resolve();

async function applyChange(
  queryClient: QueryClient,
  change: DefaultProfileChange,
): Promise<void> {
  const { backend } = getActiveBackend();
  if (backend.kind !== "local" || isNoBackend(backend)) return;
  await settleRunningDefaultAgentProfileMigration(
    queryClient,
    backend.id,
  ).catch(() => undefined);
  const stored = await AgentProfilesService.getProfile(
    WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME,
  )
    .then((detail) => detail.profile)
    .catch((error: unknown) => {
      if (error instanceof HttpError && error.status === 404) return null;
      throw error;
    });
  const patch = stored ? change(stored) : null;
  if (!stored || !patch) return;
  await AgentProfilesService.saveProfile(
    WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME,
    mergeAgentProfileSaveInput(stored, {
      agent_kind: stored.agent_kind,
      ...patch,
    } as AgentProfileSaveInput),
  );
  await queryClient.invalidateQueries({
    queryKey: AGENT_PROFILES_QUERY_KEYS.all,
  });
}

/**
 * Apply a global list edit to the local `default` profile too. Edits run one
 * at a time, so each reads the previous one's result. A failure is toasted,
 * since the global edit itself already saved.
 */
export function updateDefaultAgentProfile(
  queryClient: QueryClient,
  change: DefaultProfileChange,
): Promise<void> {
  queue = queue
    .then(() => applyChange(queryClient, change))
    .catch((error: unknown) => {
      console.error("Failed to update the default agent profile:", error);
      displayErrorToast(i18n.t(I18nKey.SETTINGS$DEFAULT_PROFILE_NOT_UPDATED));
    });
  return queue;
}

type McpRefs = { mcp_server_refs?: string[] | null };

/** An unrestricted `default` already loads every server. */
export const mcpServerAdded =
  (name: string): DefaultProfileChange =>
  (profile) => {
    const refs = (profile as McpRefs).mcp_server_refs;
    return refs && !refs.includes(name)
      ? { mcp_server_refs: [...refs, name] }
      : null;
  };

export const mcpServerRenamed =
  (from: string, to: string): DefaultProfileChange =>
  (profile) => {
    const refs = (profile as McpRefs).mcp_server_refs;
    return refs?.includes(from)
      ? { mcp_server_refs: refs.map((ref) => (ref === from ? to : ref)) }
      : null;
  };

export const mcpServerRemoved =
  (name: string): DefaultProfileChange =>
  (profile) => {
    const refs = (profile as McpRefs).mcp_server_refs;
    return refs?.includes(name)
      ? { mcp_server_refs: refs.filter((ref) => ref !== name) }
      : null;
  };

/** Switch the skills whose state differs between two selections the same way on `default`. */
export const skillSelectionChanged =
  (previous: SkillEnablement, next: SkillEnablement): DefaultProfileChange =>
  (profile) => {
    if (profile.agent_kind !== "openhands") return null;
    const wasOn = buildSkillEnablementFilter(previous);
    const isOn = buildSkillEnablementFilter(next);
    const names = new Set([
      ...CATALOG_SKILL_NAMES,
      ...(previous.enabledSkills ?? []),
      ...(next.enabledSkills ?? []),
      ...(previous.disabledSkills ?? []),
      ...(next.disabledSkills ?? []),
    ]);
    const stored = profileSkillEnablement(profile);
    const updated = [...names]
      .filter((name) => wasOn(name) !== isOn(name))
      .reduce(
        (selection, name) => toggleSkill(selection, name, isOn(name)),
        stored,
      );
    return sameSkillSelection(stored, updated)
      ? null
      : toProfileSkillFields(updated);
  };
