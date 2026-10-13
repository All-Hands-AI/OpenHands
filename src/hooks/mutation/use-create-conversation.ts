import { useMutation, useQueryClient } from "@tanstack/react-query";
import AgentServerConversationService from "#/api/conversation-service/agent-server-conversation-service.api";
import { PluginSpec } from "#/api/conversation-service/agent-server-conversation-service.types";
import { SuggestedTask } from "#/utils/types";
import { Provider } from "#/types/settings";
import { useTracking } from "#/hooks/use-tracking";
import { useLlmProfiles } from "#/hooks/query/use-llm-profiles";
import { useAgentProfiles } from "#/hooks/query/use-agent-profiles";
import { useSettings } from "#/hooks/query/use-settings";
import { useMetaProfiles } from "#/hooks/query/use-meta-profiles";
import { useActiveBackend } from "#/contexts/active-backend-context";
import PluginsManagementService, {
  type InstalledPluginInfo,
} from "#/api/plugins-management-service";
import { PLUGINS_QUERY_KEYS } from "#/hooks/query/query-keys";
import {
  launchProfileOptions,
  resolveConversationLaunch,
} from "#/hooks/mutation/resolve-conversation-launch";
import { pluginReferenceKey } from "#/utils/plugin-display";
import {
  getStoredConversationMetadata,
  setStoredConversationMetadata,
  toPluginCoordinates,
  type WorkspaceMode,
} from "#/api/conversation-metadata-store";

export interface CreateConversationVariables {
  query?: string;
  automationSetup?: boolean;
  automationSetupTags?: Record<string, string>;
  repository?: {
    name: string;
    gitProvider: Provider;
    branch?: string;
  };
  suggestedTask?: SuggestedTask;
  conversationInstructions?: string;
  parentConversationId?: string;
  agentType?: "default" | "plan";
  plugins?: PluginSpec[];
  workingDir?: string;
  workspaceMode?: WorkspaceMode;
  // Launch from a specific AgentProfile (local backend). When omitted, the
  // active AgentProfile (if any) is used so home-composed conversations
  // launch from the user's selected profile (#3727).
  agentProfileId?: string;
  entryPoint?: string; // analytics only; not forwarded to the service
}

export const CREATE_CONVERSATION_MUTATION_KEY = ["create-conversation"];

interface CreateConversationResponse {
  conversation_id: string;
  session_api_key: string | null;
  url: string | null;
  task_id?: string;
}

interface UseCreateConversationOptions {
  /**
   * Set by callers that report a failed create themselves, so the global
   * mutation error toast doesn't repeat it.
   */
  disableToast?: boolean;
}

export const useCreateConversation = ({
  disableToast = false,
}: UseCreateConversationOptions = {}) => {
  const queryClient = useQueryClient();
  const { trackConversationCreated } = useTracking();
  // Cache-warm on the home page (the profile picker reads the same query).
  // Stamped onto the conversation at creation so the switcher can show the
  // exact profile even when several profiles share a model (#1082).
  const { data: llmProfiles } = useLlmProfiles();
  // Warm the agent-profiles cache too — the launch path below awaits the same
  // query via ensureQueryData, so a warm cache makes home-launch instant. The
  // hook's maybe-unresolved data is deliberately NOT read at launch time:
  // activation is pointer-only (it never writes agent_settings), so racing a
  // cold cache into the agent_settings fallback would silently launch the
  // wrong agent.
  const { backend, orgId } = useActiveBackend();
  useAgentProfiles();
  // Read the "Run on first message" toggle from the warmed settings
  // query so the cloud path can stamp the router instruction without a
  // settings round-trip at conversation creation. The local path reads the
  // toggle from its own settings fetch inside the encrypted-settings builder.
  const { data: settings } = useSettings();
  // The active meta-profile gates the suffix on the cloud path: with no
  // active router the agent-server does not attach `route_task_to_model`, so
  // emitting the instruction would tell the agent to call a tool it lacks.
  const { data: metaProfiles } = useMetaProfiles();

  return useMutation({
    mutationKey: CREATE_CONVERSATION_MUTATION_KEY,
    meta: { disableToast },
    mutationFn: async (
      variables: CreateConversationVariables,
    ): Promise<CreateConversationResponse> => {
      const {
        query,
        automationSetup,
        automationSetupTags,
        conversationInstructions,
        plugins,
        repository,
        workingDir,
        workspaceMode,
        parentConversationId,
        agentType,
        agentProfileId,
      } = variables;

      // The active AgentProfile is the default launch profile for new
      // conversations (#3727), on both local and cloud.
      const launch = await resolveConversationLaunch({
        queryClient,
        backendId: backend.id,
        orgId,
        isCloud: backend.kind === "cloud",
        agentProfileId,
      });

      // Only extend the call with the profile fields when launching from a
      // profile, so a plain create stays byte-identical to the legacy
      // agent_settings path (#3727). sandboxId is unused here.
      const conversation =
        await AgentServerConversationService.createConversation({
          initialUserMsg: query,
          automationSetup,
          ...(automationSetupTags ? { automationSetupTags } : {}),
          conversationInstructions,
          plugins,
          metadata: repository
            ? {
                selected_repository: repository.name,
                selected_branch: repository.branch ?? null,
                git_provider: repository.gitProvider,
              }
            : null,
          workingDirOverride: workingDir,
          workspaceMode,
          parentConversationId,
          agentType,
          ...launchProfileOptions(launch),
          // Only stamp the toggle when it's on so the default path stays
          // byte-identical to the legacy launch (and the e2e snapshot tests
          // that assert the exact createConversation payload). The active
          // meta-profile gates the suffix: no router attached means no
          // route-at-start instruction, even if the toggle was left on.
          ...(settings?.run_router_at_conversation_start
            ? {
                runRouterAtConversationStart: true,
                hasActiveMetaProfile: !!metaProfiles?.active_meta_profile,
              }
            : {}),
        });

      // Stamp the active LLM profile onto the (local) conversation so the
      // chat switcher shows the exact profile even when several profiles
      // share a model (#1082). Cloud conversations don't use local profiles
      // (app_conversation_id stays null until the sandbox is READY). Merge so
      // the repo/workspace metadata the service just persisted is preserved.
      const localConversationId = conversation.app_conversation_id;
      // Snapshot the conversation's plugins into client-side metadata so the
      // in-conversation plugins view can show what's loaded (coordinates only
      // — strip parameters, which may carry secrets). The agent-server doesn't
      // return a live conversation's loaded plugins, so this snapshot is the
      // source for that view. Two sources, deduped by coordinates:
      //   1. plugins explicitly attached at creation (e.g. the /launch flow);
      //   2. enabled installed plugins, which the SDK auto-loads into every new
      //      local conversation (see use-set-plugin-enabled).
      const explicitPlugins = plugins?.map(toPluginCoordinates) ?? [];
      let attachedPlugins: PluginSpec[] = explicitPlugins;
      if (localConversationId) {
        let installed: InstalledPluginInfo[] = [];
        try {
          installed = await queryClient.ensureQueryData({
            // Same key `usePlugins` writes. Unscoped, this served the previous
            // backend's list and attached plugins the target server lacks.
            queryKey: [...PLUGINS_QUERY_KEYS.installed, backend.id, orgId],
            queryFn: () => PluginsManagementService.listInstalledPlugins(),
          });
        } catch {
          // Best-effort: never let plugin lookup block conversation creation.
        }
        const seen = new Set(explicitPlugins.map(pluginReferenceKey));
        const enabledInstalled = installed
          .filter((plugin) => plugin.enabled)
          .map((plugin) => ({
            source: plugin.source,
            ref: plugin.resolved_ref ?? null,
            repo_path: plugin.repo_path ?? null,
            // Keep the human-friendly name so the plugins view shows e.g.
            // "city-weather" rather than deriving "local" from the source.
            name: plugin.name,
          }))
          .filter((plugin) => !seen.has(pluginReferenceKey(plugin)));
        attachedPlugins = [...explicitPlugins, ...enabledInstalled];
      }
      // Stamp the LLM profile the conversation runs so the switcher pill names
      // it exactly (#1082). agent_settings launches run the active LLM; ACP
      // profiles carry none (unused by the ACP model chip).
      const activeProfile =
        launch.llmProfile ??
        launch.activeLlmProfile ??
        llmProfiles?.active_profile ??
        null;
      if (localConversationId && (activeProfile || attachedPlugins.length)) {
        const prev = getStoredConversationMetadata(localConversationId);
        setStoredConversationMetadata(localConversationId, {
          selected_repository: prev?.selected_repository ?? null,
          selected_branch: prev?.selected_branch ?? null,
          git_provider: prev?.git_provider ?? null,
          selected_workspace: prev?.selected_workspace ?? null,
          workspace_mode: prev?.workspace_mode ?? null,
          active_profile: activeProfile ?? prev?.active_profile ?? null,
          plugins: attachedPlugins.length
            ? attachedPlugins
            : (prev?.plugins ?? null),
        });
      }

      // OpenHands cloud pattern: when the start task isn't immediately
      // READY (cloud sandbox is still provisioning),
      // app_conversation_id is null. We return a `task-{id}` URL so the
      // conversation route's useTaskPolling can drive it to READY and
      // then redirect to the real `/conversations/{app_conversation_id}`.
      const conversationId = conversation.app_conversation_id
        ? conversation.app_conversation_id
        : `task-${conversation.id}`;

      return {
        conversation_id: conversationId,
        session_api_key: null,
        url: conversation.agent_server_url,
        task_id: conversation.id,
      };
    },
    onSuccess: async (data, variables) => {
      trackConversationCreated({
        conversationId: data.conversation_id,
        taskId: data.task_id,
        hasRepository: !!variables.repository,
        gitProvider: variables.repository?.gitProvider,
        hasWorkspace: !!variables.workingDir,
        workspaceMode: variables.workspaceMode,
        hasInitialQuery: !!variables.query,
        agentType: variables.agentType,
        hasParentConversation: !!variables.parentConversationId,
        entryPoint: variables.entryPoint,
      });

      // Invalidate (rather than remove) so the existing paginated list stays
      // rendered while a background refetch picks up the new conversation.
      // `removeQueries` would wipe the cache and force the panel back to its
      // initial loading state, dropping loaded pages and scroll position.
      queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
      // The cloud path returns a start task (no app_conversation_id
      // yet); the sidebar surfaces those via `useStartTasks` which doesn't
      // poll, so invalidate it explicitly so the in-flight task shows up
      // in the conversation list immediately.
      queryClient.invalidateQueries({
        queryKey: ["start-tasks"],
      });
    },
  });
};
