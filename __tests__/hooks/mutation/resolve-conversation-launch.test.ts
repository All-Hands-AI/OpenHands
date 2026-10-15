import { QueryClient } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import { resolveConversationLaunch } from "#/hooks/mutation/resolve-conversation-launch";

const { listAgentProfiles, listLlmProfiles, supportsOverride } = vi.hoisted(
  () => ({
    listAgentProfiles: vi.fn(),
    listLlmProfiles: vi.fn(),
    supportsOverride: vi.fn(),
  }),
);

vi.mock("#/api/agent-profiles-service/agent-profiles-service.api", () => ({
  __esModule: true,
  default: { listProfiles: listAgentProfiles, getProfile: vi.fn() },
  WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME: "default",
}));
vi.mock("#/api/profiles-service/profiles-service.api", () => ({
  __esModule: true,
  default: { listProfiles: listLlmProfiles },
}));
vi.mock("#/api/agent-server-adapter", () => ({
  backendSupportsLaunchLlmOverride: supportsOverride,
}));

const PARENT_PROFILE = {
  id: "profile-1",
  name: "reviewer",
  agent_kind: "openhands",
  revision: 1,
  llm_profile_ref: "slow",
  mcp_server_refs: null,
};

function launchWithParentModel() {
  return resolveConversationLaunch({
    queryClient: new QueryClient(),
    backendId: "local-1",
    orgId: null,
    isCloud: false,
    agentProfileId: "profile-1",
    llmProfile: "fast",
  });
}

describe("resolveConversationLaunch with a requested LLM profile", () => {
  afterEach(() => vi.resetAllMocks());

  it("runs the requested LLM on the picked profile", async () => {
    listAgentProfiles.mockResolvedValue({
      profiles: [PARENT_PROFILE],
      active_agent_profile_id: null,
    });
    listLlmProfiles.mockResolvedValue({
      profiles: [{ name: "slow" }, { name: "fast" }],
      active_profile: "slow",
    });
    supportsOverride.mockResolvedValue(true);

    await expect(launchWithParentModel()).resolves.toMatchObject({
      agentProfileId: "profile-1",
      llmProfileOverride: "fast",
      llmProfile: "fast",
    });
  });

  it("keeps the profile on its own LLM when the server has no override", async () => {
    listAgentProfiles.mockResolvedValue({
      profiles: [PARENT_PROFILE],
      active_agent_profile_id: null,
    });
    listLlmProfiles.mockResolvedValue({
      profiles: [{ name: "slow" }, { name: "fast" }],
      active_profile: "slow",
    });
    supportsOverride.mockResolvedValue(false);

    const launch = await launchWithParentModel();

    expect(launch).toMatchObject({
      agentProfileId: "profile-1",
      llmProfile: "slow",
    });
    expect(launch.llmProfileOverride).toBeUndefined();
  });
});
