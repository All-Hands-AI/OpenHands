import { QueryClient } from "@tanstack/react-query";
import { HttpError } from "@openhands/typescript-client";
import { DEFAULT_ENABLED_SKILL_NAMES } from "@openhands/extensions/skills";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AgentProfilesService from "#/api/agent-profiles-service/agent-profiles-service.api";
import { getActiveBackend } from "#/api/backend-registry/active-store";
import {
  mcpServerAdded,
  mcpServerRemoved,
  mcpServerRenamed,
  skillSelectionChanged,
  updateDefaultAgentProfile,
} from "#/hooks/mutation/update-default-agent-profile";
import { settleRunningDefaultAgentProfileMigration } from "#/hooks/use-migrate-default-agent-profile";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { CATALOG_SKILL_NAMES } from "#/utils/skill-enablement";

vi.mock("#/api/agent-profiles-service/agent-profiles-service.api", () => ({
  __esModule: true,
  default: { getProfile: vi.fn(), saveProfile: vi.fn() },
  WELL_KNOWN_DEFAULT_AGENT_PROFILE_NAME: "default",
}));
vi.mock("#/api/backend-registry/active-store", () => ({
  getActiveBackend: vi.fn(),
  isNoBackend: (backend: { id: string }) => backend.id === "no-backend",
}));
vi.mock("#/hooks/use-migrate-default-agent-profile", () => ({
  settleRunningDefaultAgentProfileMigration: vi.fn(),
}));
vi.mock("#/utils/custom-toast-handlers", () => ({
  displayErrorToast: vi.fn(),
}));

const [ON, OFF] = [
  DEFAULT_ENABLED_SKILL_NAMES[0],
  CATALOG_SKILL_NAMES.find(
    (name) => !DEFAULT_ENABLED_SKILL_NAMES.includes(name),
  )!,
];

const openHandsDefault = (overrides: Record<string, unknown> = {}) => ({
  id: "id-default",
  name: "default",
  revision: 3,
  agent_kind: "openhands",
  llm_profile_ref: "llm",
  mcp_server_refs: null,
  public_skills: [...DEFAULT_ENABLED_SKILL_NAMES],
  disabled_skills: [],
  ...overrides,
});

const useBackend = (kind: "local" | "cloud", id = "local-1") =>
  vi.mocked(getActiveBackend).mockReturnValue({
    backend: { id, kind },
  } as never);

const storeDefault = (profile: Record<string, unknown>) =>
  vi
    .mocked(AgentProfilesService.getProfile)
    .mockResolvedValue({ name: "default", profile } as never);

describe("default profile list changes", () => {
  it("leaves an unrestricted default alone, since it already loads every MCP server", () => {
    const profile = openHandsDefault() as never;
    expect(mcpServerAdded("linear")(profile)).toBeNull();
    expect(mcpServerRenamed("github", "gh")(profile)).toBeNull();
    expect(mcpServerRemoved("github")(profile)).toBeNull();
  });

  it("adds, renames and drops a server in a restricted default, ACP included", () => {
    const profile = {
      ...openHandsDefault({ mcp_server_refs: ["github", "slack"] }),
      agent_kind: "acp",
    } as never;
    expect(mcpServerAdded("linear")(profile)).toEqual({
      mcp_server_refs: ["github", "slack", "linear"],
    });
    expect(mcpServerRenamed("github", "gh")(profile)).toEqual({
      mcp_server_refs: ["gh", "slack"],
    });
    expect(mcpServerRemoved("github")(profile)).toEqual({
      mcp_server_refs: ["slack"],
    });
    expect(mcpServerAdded("github")(profile)).toBeNull();
    expect(mcpServerRemoved("linear")(profile)).toBeNull();
  });

  it("switches only the skills the Skills page changed, keeping default's own picks", () => {
    const page = {
      enabledSkills: [...DEFAULT_ENABLED_SKILL_NAMES],
      disabledSkills: [],
    };
    const profile = openHandsDefault({
      public_skills: DEFAULT_ENABLED_SKILL_NAMES.filter((name) => name !== ON),
      disabled_skills: ["my-skill"],
    }) as never;

    const patch = skillSelectionChanged(page, {
      enabledSkills: [...page.enabledSkills, OFF],
      disabledSkills: ["user-skill"],
    })(profile) as { public_skills: string[]; disabled_skills: string[] };

    expect([...patch.public_skills].sort()).toEqual(
      [
        ...DEFAULT_ENABLED_SKILL_NAMES.filter((name) => name !== ON),
        OFF,
      ].sort(),
    );
    expect([...patch.disabled_skills].sort()).toEqual([
      "my-skill",
      "user-skill",
    ]);
  });

  it("returns null when default already has the change, or is an ACP profile", () => {
    const page = { enabledSkills: [ON], disabledSkills: [] };
    const turnedOff = { enabledSkills: [], disabledSkills: [] };
    const without = openHandsDefault({ public_skills: [] }) as never;
    expect(skillSelectionChanged(page, turnedOff)(without)).toBeNull();
    expect(
      skillSelectionChanged(
        page,
        turnedOff,
      )({
        ...openHandsDefault(),
        agent_kind: "acp",
      } as never),
    ).toBeNull();
  });
});

describe("updateDefaultAgentProfile", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient();
    useBackend("local");
    vi.mocked(settleRunningDefaultAgentProfileMigration).mockResolvedValue(
      undefined,
    );
    vi.mocked(AgentProfilesService.saveProfile).mockResolvedValue({} as never);
  });

  it("saves the change over the stored default after its migration", async () => {
    storeDefault(openHandsDefault({ mcp_server_refs: ["github"] }));

    await updateDefaultAgentProfile(queryClient, mcpServerAdded("linear"));

    expect(settleRunningDefaultAgentProfileMigration).toHaveBeenCalledWith(
      queryClient,
      "local-1",
    );
    const [name, saved] = vi.mocked(AgentProfilesService.saveProfile).mock
      .calls[0];
    expect(name).toBe("default");
    expect(saved).toMatchObject({
      agent_kind: "openhands",
      llm_profile_ref: "llm",
      mcp_server_refs: ["github", "linear"],
    });
    expect(saved).not.toHaveProperty("revision");
  });

  it("does nothing on Cloud, without a default, or when nothing changes", async () => {
    useBackend("cloud");
    await updateDefaultAgentProfile(queryClient, mcpServerAdded("linear"));
    expect(AgentProfilesService.getProfile).not.toHaveBeenCalled();

    useBackend("local");
    vi.mocked(AgentProfilesService.getProfile).mockRejectedValueOnce(
      new HttpError(404, "Not Found", {}, "missing"),
    );
    await updateDefaultAgentProfile(queryClient, mcpServerAdded("linear"));
    storeDefault(openHandsDefault());
    await updateDefaultAgentProfile(queryClient, mcpServerAdded("linear"));

    expect(AgentProfilesService.saveProfile).not.toHaveBeenCalled();
    expect(displayErrorToast).not.toHaveBeenCalled();
  });

  it("runs changes one at a time, so the second reads the first's save", async () => {
    let stored = openHandsDefault({ mcp_server_refs: [] as string[] });
    vi.mocked(AgentProfilesService.getProfile).mockImplementation(
      async () => ({ name: "default", profile: stored }) as never,
    );
    vi.mocked(AgentProfilesService.saveProfile).mockImplementation(
      async (_name, profile) => {
        await new Promise((resolve) => {
          setTimeout(resolve, 5);
        });
        stored = { ...stored, ...(profile as typeof stored) };
        return {} as never;
      },
    );

    await Promise.all([
      updateDefaultAgentProfile(queryClient, mcpServerAdded("a")),
      updateDefaultAgentProfile(queryClient, mcpServerAdded("b")),
    ]);

    expect(stored.mcp_server_refs).toEqual(["a", "b"]);
  });

  it("toasts a failed save and keeps later changes running", async () => {
    storeDefault(openHandsDefault({ mcp_server_refs: ["github"] }));
    vi.mocked(AgentProfilesService.saveProfile).mockRejectedValueOnce(
      new Error("boom"),
    );
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    await updateDefaultAgentProfile(queryClient, mcpServerAdded("linear"));
    await updateDefaultAgentProfile(queryClient, mcpServerRemoved("github"));

    expect(displayErrorToast).toHaveBeenCalledTimes(1);
    expect(AgentProfilesService.saveProfile).toHaveBeenCalledTimes(2);
  });
});
