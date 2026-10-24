import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AgentProfilesService from "#/api/agent-profiles-service/agent-profiles-service.api";
import SettingsService from "#/api/settings-service/settings-service.api";
import { useActivateAgentProfile } from "#/hooks/mutation/use-activate-agent-profile";
import { displayErrorToast } from "#/utils/custom-toast-handlers";

vi.mock("#/api/agent-profiles-service/agent-profiles-service.api", () => ({
  __esModule: true,
  default: {
    activateProfile: vi.fn(),
    listProfiles: vi.fn(),
    getProfile: vi.fn(),
  },
}));
vi.mock("#/api/settings-service/settings-service.api", () => ({
  __esModule: true,
  default: { saveSettings: vi.fn(), invalidateCache: vi.fn() },
}));
vi.mock("#/utils/custom-toast-handlers", () => ({
  displayErrorToast: vi.fn(),
}));

const useActiveBackendMock = vi.hoisted(() => vi.fn());
vi.mock("#/contexts/active-backend-context", () => ({
  useActiveBackend: () => useActiveBackendMock(),
}));

const useBackend = (kind: "cloud" | "local") =>
  useActiveBackendMock.mockReturnValue({
    backend: { id: "bk-1", kind },
    orgId: null,
  });

const openHandsSummary = {
  id: "prof-oh",
  name: "default",
  agent_kind: "openhands",
  revision: 1,
  llm_profile_ref: "llm",
  mcp_server_refs: null,
};

const acpSummary = {
  id: "prof-acp",
  name: "claude",
  agent_kind: "acp",
  revision: 2,
  llm_profile_ref: null,
  mcp_server_refs: null,
};

const openHandsDetail = {
  name: "default",
  profile: {
    agent_kind: "openhands",
    id: "prof-oh",
    name: "default",
    revision: 1,
    mcp_server_refs: null,
    llm_profile_ref: "llm",
  },
};

const acpDetail = {
  name: "claude",
  profile: {
    agent_kind: "acp",
    id: "prof-acp",
    name: "claude",
    revision: 2,
    mcp_server_refs: null,
    acp_server: "claude-code",
    acp_model: "claude-x",
    acp_session_mode: null,
    acp_prompt_timeout: 60,
    acp_command: null,
    acp_args: null,
  },
};

const activateResponse = {
  id: "prof-oh",
  message: "Profile activated",
  agent_settings_applied: false,
};

const renderActivateHook = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
  const { result } = renderHook(() => useActivateAgentProfile(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
  return { result, invalidateSpy };
};

const activate = async (profileId: string) => {
  const { result, invalidateSpy } = renderActivateHook();
  result.current.mutate(profileId);
  await waitFor(() => expect(result.current.isPending).toBe(false));
  return { result, invalidateSpy };
};

describe("useActivateAgentProfile agent-kind sync (#18883)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBackend("cloud");
  });

  it("on cloud, activating an OpenHands profile writes agent_kind openhands into agent_settings", async () => {
    vi.mocked(AgentProfilesService.activateProfile).mockResolvedValue(
      activateResponse,
    );
    vi.mocked(AgentProfilesService.listProfiles).mockResolvedValue({
      profiles: [openHandsSummary],
      active_agent_profile_id: "prof-oh",
    } as never);
    vi.mocked(AgentProfilesService.getProfile).mockResolvedValue(
      openHandsDetail as never,
    );

    const { invalidateSpy } = await activate("prof-oh");

    expect(AgentProfilesService.activateProfile).toHaveBeenCalledWith(
      "prof-oh",
    );
    expect(SettingsService.saveSettings).toHaveBeenCalledWith({
      agent_settings_diff: { agent_kind: "openhands" },
    });
    // The activation's own defensive cache refresh still runs after the sync.
    expect(invalidateSpy).toHaveBeenCalled();
  });

  it("on cloud, activating an ACP profile re-states the profile's own provider fields", async () => {
    vi.mocked(AgentProfilesService.activateProfile).mockResolvedValue({
      ...activateResponse,
      id: "prof-acp",
    });
    vi.mocked(AgentProfilesService.listProfiles).mockResolvedValue({
      profiles: [acpSummary],
      active_agent_profile_id: "prof-acp",
    } as never);
    vi.mocked(AgentProfilesService.getProfile).mockResolvedValue(
      acpDetail as never,
    );

    await activate("prof-acp");

    expect(AgentProfilesService.getProfile).toHaveBeenCalledWith("claude");
    expect(SettingsService.saveSettings).toHaveBeenCalledWith({
      agent_settings_diff: {
        agent_kind: "acp",
        acp_server: "claude-code",
        acp_command: [],
        acp_args: [],
        acp_model: "claude-x",
      },
    });
  });

  it("on local, activation does not write agent_settings", async () => {
    useBackend("local");
    vi.mocked(AgentProfilesService.activateProfile).mockResolvedValue(
      activateResponse,
    );

    await activate("prof-oh");

    expect(AgentProfilesService.activateProfile).toHaveBeenCalledWith(
      "prof-oh",
    );
    expect(AgentProfilesService.listProfiles).not.toHaveBeenCalled();
    expect(AgentProfilesService.getProfile).not.toHaveBeenCalled();
    expect(SettingsService.saveSettings).not.toHaveBeenCalled();
  });

  it("a failed kind sync toasts but does not fail the activation", async () => {
    vi.mocked(AgentProfilesService.activateProfile).mockResolvedValue(
      activateResponse,
    );
    vi.mocked(AgentProfilesService.listProfiles).mockResolvedValue({
      profiles: [openHandsSummary],
      active_agent_profile_id: "prof-oh",
    } as never);
    vi.mocked(AgentProfilesService.getProfile).mockResolvedValue(
      openHandsDetail as never,
    );
    vi.mocked(SettingsService.saveSettings).mockRejectedValue(
      new Error("settings write failed"),
    );

    const { result, invalidateSpy } = await activate("prof-oh");

    // Activation completes even though the sync failed.
    expect(result.current.isSuccess).toBe(true);
    expect(SettingsService.saveSettings).toHaveBeenCalledOnce();
    expect(displayErrorToast).toHaveBeenCalled();
    // The activation's own defensive invalidations still run.
    expect(invalidateSpy).toHaveBeenCalled();
  });

  it("a failed profile lookup skips the sync and keeps the activation successful", async () => {
    vi.mocked(AgentProfilesService.activateProfile).mockResolvedValue(
      activateResponse,
    );
    vi.mocked(AgentProfilesService.listProfiles).mockRejectedValue(
      new Error("list failed"),
    );

    const { result } = await activate("prof-oh");

    expect(result.current.isSuccess).toBe(true);
    expect(SettingsService.saveSettings).not.toHaveBeenCalled();
    expect(displayErrorToast).not.toHaveBeenCalled();
  });
});
