import type { QueryClient } from "@tanstack/react-query";
import type { AgentKind } from "@openhands/typescript-client";
import AgentProfilesService, {
  WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME,
  type AgentProfileListResponse,
} from "#/api/agent-profiles-service/agent-profiles-service.api";
import ProfilesService from "#/api/profiles-service/profiles-service.api";
import { backendSupportsLaunchLlmOverride } from "#/api/agent-server-adapter";
import type { CreateConversationOptions } from "#/api/conversation-service/agent-server-conversation-service.api";
import {
  AGENT_PROFILES_QUERY_KEYS,
  AGENT_PROFILES_RETRY_OPTIONS,
  LLM_PROFILES_QUERY_KEYS,
} from "#/hooks/query/query-keys";

export interface ConversationLaunch {
  /** Unset when the launch sends the global `agent_settings` instead. */
  agentProfileId?: string;
  agentProfileKind?: AgentKind;
  /** Runs the agent profile with this LLM profile instead of its own. */
  llmProfileOverride?: string;
  /** The LLM profile an OpenHands profile launch runs. */
  llmProfile?: string;
  /** The account-wide active LLM profile, when resolution read it. */
  activeLlmProfile: string | null;
}

interface ResolveConversationLaunchOptions {
  queryClient: QueryClient;
  backendId: string;
  orgId: string | null | undefined;
  isCloud: boolean;
  /** An explicit profile pick; omitted launches the active profile. */
  agentProfileId?: string;
  /** The LLM profile to run, such as a parent conversation's current model. */
  llmProfile?: string | null;
}

/** Decide which agent source and LLM a new conversation launches with. */
export async function resolveConversationLaunch({
  queryClient,
  backendId,
  orgId,
  isCloud,
  agentProfileId,
  llmProfile,
}: ResolveConversationLaunchOptions): Promise<ConversationLaunch> {
  // Await the list from the shared query cache: a send fired before the home
  // query resolves must still launch from the active profile. Do not fall back
  // to the global agent_settings when profile discovery fails: activation is
  // pointer-only, so those settings may describe a different agent.
  const agentProfiles: AgentProfileListResponse =
    await queryClient.ensureQueryData({
      queryKey: [...AGENT_PROFILES_QUERY_KEYS.all, backendId, orgId],
      queryFn: AgentProfilesService.listProfiles,
      ...AGENT_PROFILES_RETRY_OPTIONS,
      // A failure here rejects the launch, which reports it.
      meta: { disableToast: true },
    });

  const requestedAgentProfileId =
    agentProfileId ?? agentProfiles.active_agent_profile_id ?? undefined;
  const profile = requestedAgentProfileId
    ? agentProfiles.profiles?.find((p) => p.id === requestedAgentProfileId)
    : undefined;

  let prefersAgentSettings = false;
  let activeLlmProfile: string | null = null;
  let llmProfileOverride: string | undefined;
  if (
    !isCloud &&
    profile?.name === WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME &&
    profile.agent_kind === "openhands"
  ) {
    // The seeded OpenHands `default` launches via agent_settings so the Skills
    // page selection (buildAgentContext) applies: a profile launch gets the
    // server's whole skill catalog minus a deny-list. Per-profile fields saved
    // on `default` therefore don't apply on local launches.
    //
    // Scoped to OpenHands: global agent_settings is stale when an ACP profile
    // is active. Scoped to local: cloud always resolves `default` server-side.
    prefersAgentSettings = true;
  } else if (profile?.agent_kind === "openhands" && profile.llm_profile_ref) {
    // Await the list rather than a render snapshot: a send fired before the
    // LLM-profile query loads must still validate the ref.
    let llmProfileExists = false;
    try {
      const llm = await queryClient.ensureQueryData({
        queryKey: [...LLM_PROFILES_QUERY_KEYS.all, backendId, orgId],
        queryFn: ProfilesService.listProfiles,
        retry: false,
        meta: { disableToast: true },
      });
      llmProfileExists = llm.profiles.some(
        (p) => p.name === profile.llm_profile_ref,
      );
      activeLlmProfile = llm.active_profile ?? null;
    } catch {
      // Unvalidated; handled below.
    }
    // The home LLM pill shows and activates the account-wide active LLM
    // profile, never the pinned ref (#16539), so an implicit launch runs that
    // selection. An explicit pick keeps its pinned ref unless the ref is gone.
    const preferredLlmProfile =
      llmProfile ||
      (!agentProfileId || !llmProfileExists ? activeLlmProfile : null);
    const selectedLlmProfile =
      !isCloud &&
      preferredLlmProfile &&
      preferredLlmProfile !== profile.llm_profile_ref
        ? preferredLlmProfile
        : undefined;
    if (!llmProfileExists || selectedLlmProfile) {
      if (!isCloud && (await backendSupportsLaunchLlmOverride())) {
        // A dangling ref with nothing selected reaches the server, which
        // rejects it with an error the user can act on.
        llmProfileOverride = selectedLlmProfile;
      } else if (!llmProfileExists || !llmProfile) {
        // No per-launch override on this server: run agent_settings at the
        // cost of the profile's other fields. A requested LLM is dropped
        // instead, keeping the profile.
        if (!llmProfileExists) {
          console.warn(
            `Agent profile "${profile.name}" references missing ` +
              `LLM profile "${profile.llm_profile_ref}"; ` +
              "launching from agent_settings instead.",
          );
        }
        prefersAgentSettings = true;
      }
    }
  }

  // A legacy agent_settings launch carries no profile identity, so Agent
  // Server cannot enforce that profile's secret allow-list. Keep restricted
  // profiles on the server-resolved path; if the detail cannot be read, fail
  // closed and let Agent Server report the underlying error.
  let profileAllowsAgentSettings = true;
  if (prefersAgentSettings && profile) {
    try {
      const detail = await queryClient.fetchQuery({
        queryKey: AGENT_PROFILES_QUERY_KEYS.detail(
          backendId,
          orgId,
          profile.name,
        ),
        queryFn: () => AgentProfilesService.getProfile(profile.name),
        ...AGENT_PROFILES_RETRY_OPTIONS,
        meta: { disableToast: true },
      });
      const secretRefs = (detail.profile as { secret_refs?: unknown })
        .secret_refs;
      profileAllowsAgentSettings = !Array.isArray(secretRefs);
    } catch {
      profileAllowsAgentSettings = false;
    }
  }

  if (
    !requestedAgentProfileId ||
    (prefersAgentSettings && profileAllowsAgentSettings)
  ) {
    return { activeLlmProfile };
  }
  return {
    agentProfileId: requestedAgentProfileId,
    agentProfileKind: profile?.agent_kind,
    llmProfileOverride,
    llmProfile:
      profile?.agent_kind === "openhands"
        ? (llmProfileOverride ?? profile.llm_profile_ref ?? undefined)
        : undefined,
    activeLlmProfile,
  };
}

/** The `createConversation` options that carry a resolved launch. */
export function launchProfileOptions(
  launch: ConversationLaunch,
): Partial<CreateConversationOptions> {
  if (!launch.agentProfileId) return {};
  return {
    agentProfileId: launch.agentProfileId,
    agentProfileKind: launch.agentProfileKind,
    // Title generation uses the same LLM as the agent (#16885).
    agentLlmProfileRef: launch.llmProfile,
    ...(launch.llmProfileOverride
      ? { agentLlmProfileOverride: launch.llmProfileOverride }
      : {}),
  };
}
