import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  __resetActiveStoreForTests,
  setActiveSelection,
  setRegisteredBackends,
} from "#/api/backend-registry/active-store";
import type { Backend } from "#/api/backend-registry/types";
import AgentServerConversationService from "#/api/conversation-service/agent-server-conversation-service.api";
import { getSandboxSelectionOptions } from "#/api/cloud/sandbox-template-service.api";
import {
  getFetchCall,
  getJsonBody,
  mockJsonResponse,
} from "./fetch-test-utils";

const cloudBackend: Backend = {
  id: "prod",
  name: "Production",
  host: "https://app.all-hands.dev",
  apiKey: "bearer-token",
  kind: "cloud",
};

const originalFetch = global.fetch;
const fetchMock = vi.fn();

beforeEach(() => {
  window.localStorage.clear();
  __resetActiveStoreForTests();
  setRegisteredBackends([cloudBackend]);
  setActiveSelection({ backendId: cloudBackend.id });
  fetchMock.mockReset();
  global.fetch = fetchMock as typeof fetch;
});

afterEach(() => {
  window.localStorage.clear();
  __resetActiveStoreForTests();
  fetchMock.mockReset();
  global.fetch = originalFetch;
});

describe("AgentServerConversationService cloud branch", () => {
  it("loads template choices for the explicitly captured organization", async () => {
    setActiveSelection({ backendId: cloudBackend.id, orgId: "org-b" });
    fetchMock.mockResolvedValue(mockJsonResponse({ enabled: true, items: [] }));
    await getSandboxSelectionOptions(cloudBackend.id, "org-a");
    const [url, init] = getFetchCall(fetchMock);
    expect(url).toBe(`${cloudBackend.host}/api/v1/sandbox-specs/selection`);
    expect(init.headers).toMatchObject({ "X-Org-Id": "org-a" });
  });
  it("sends the template ID only when explicitly selected", async () => {
    fetchMock.mockImplementation(async () => mockJsonResponse({ id: "task" }));
    await AgentServerConversationService.createConversation(
      "hello", undefined, undefined, undefined, undefined, undefined,
      undefined, undefined, undefined, undefined, undefined, "monorepo_large",
    );
    expect(getJsonBody(getFetchCall(fetchMock)[1]).sandbox_spec_id).toBe("monorepo_large");
    fetchMock.mockClear();
    await AgentServerConversationService.createConversation("hello");
    expect(getJsonBody(getFetchCall(fetchMock)[1])).not.toHaveProperty("sandbox_spec_id");
  });
  it("createConversation POSTs the cloud payload directly and returns a WORKING task", async () => {
    fetchMock.mockResolvedValue(
      mockJsonResponse({
        id: "task-123",
        created_by_user_id: null,
        status: "WORKING",
        detail: null,
        app_conversation_id: null,
        agent_server_url: null,
        request: {},
        created_at: "2026-05-06T00:00:00Z",
        updated_at: "2026-05-06T00:00:00Z",
      }),
    );

    const result = await AgentServerConversationService.createConversation(
      "fix the bug",
      "Optional title",
      undefined,
      {
        selected_repository: "user/repo",
        selected_branch: "main",
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        git_provider: "github" as any,
      },
    );

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = getFetchCall(fetchMock);
    expect(url).toBe(`${cloudBackend.host}/api/v1/app-conversations`);
    expect(init).toMatchObject({
      method: "POST",
      headers: { Authorization: "Bearer bearer-token" },
    });
    const requestBody = getJsonBody(init);

    // cloud payload shape — flat fields, NO encrypted-settings round-trip.
    expect(requestBody.selected_repository).toBe("user/repo");
    expect(requestBody.selected_branch).toBe("main");
    expect(requestBody.git_provider).toBe("github");
    expect(requestBody.title).toBe("Optional title");
    expect(requestBody.initial_message).toEqual({
      role: "user",
      content: [{ type: "text", text: "fix the bug" }],
    });
    // The local-only encrypted-settings keys must NOT be present.
    expect(requestBody).not.toHaveProperty("agent_settings_encrypted");
    expect(requestBody).not.toHaveProperty("conversation_settings_encrypted");

    // The returned task is the upstream task — WORKING, no app_conversation_id yet.
    expect(result.id).toBe("task-123");
    expect(result.status).toBe("WORKING");
    expect(result.app_conversation_id).toBeNull();
  });

  it("getStartTask polls /api/v1/app-conversations/start-tasks?ids= directly", async () => {
    fetchMock.mockResolvedValue(
      mockJsonResponse([
        {
          id: "task-123",
          created_by_user_id: null,
          status: "READY",
          detail: null,
          app_conversation_id: "conv-456",
          agent_server_url: "https://runtime-456.app.all-hands.dev",
          request: {},
          created_at: "2026-05-06T00:00:00Z",
          updated_at: "2026-05-06T00:00:00Z",
        },
      ]),
    );

    const result =
      await AgentServerConversationService.getStartTask("task-123");

    const [url, init] = getFetchCall(fetchMock);
    expect(url).toBe(
      `${cloudBackend.host}/api/v1/app-conversations/start-tasks?ids=task-123`,
    );
    expect(init).toMatchObject({
      method: "GET",
      headers: { Authorization: "Bearer bearer-token" },
    });
    expect(result?.status).toBe("READY");
    expect(result?.app_conversation_id).toBe("conv-456");
  });
});
