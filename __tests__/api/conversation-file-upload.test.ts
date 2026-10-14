import { beforeEach, describe, expect, it, vi } from "vitest";
import { RemoteWorkspace } from "@openhands/typescript-client/workspace/remote-workspace";
import { HttpError } from "@openhands/typescript-client";
import {
  __resetActiveStoreForTests,
  setActiveSelection,
  setRegisteredBackends,
} from "#/api/backend-registry/active-store";
import type { Backend } from "#/api/backend-registry/types";
import { uploadFilesToConversation } from "#/api/conversation-file-upload.api";
import { clearAgentServerHomeDirCache } from "#/api/agent-server-home";
import { I18nKey } from "#/i18n/declaration";

const fileUploadMock = vi.fn();
const getHomeMock = vi.fn();
const getConversationMock = vi.fn();

vi.mock("@openhands/typescript-client/workspace/remote-workspace", () => ({
  RemoteWorkspace: vi.fn(function RemoteWorkspaceMock() {
    return { fileUpload: fileUploadMock };
  }),
}));

vi.mock("@openhands/typescript-client/clients", () => ({
  FileClient: vi.fn(function FileClientMock() {
    return { getHome: getHomeMock };
  }),
  ConversationClient: vi.fn(function ConversationClientMock() {
    return { getConversation: getConversationMock };
  }),
}));

const batchGetCloudConversations = vi.fn();

vi.mock("#/api/cloud/conversation-service.api", () => ({
  batchGetCloudConversations: (...args: unknown[]) =>
    batchGetCloudConversations(...args),
}));

const cloudBackend: Backend = {
  id: "cloud-1",
  name: "Cloud",
  host: "https://app.all-hands.dev",
  apiKey: "cloud-token",
  kind: "cloud",
};

function makeFile(name: string) {
  return new File(["content"], name, { type: "text/plain" });
}

describe("uploadFilesToConversation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    __resetActiveStoreForTests();
    clearAgentServerHomeDirCache();
    fileUploadMock.mockResolvedValue(undefined);
    batchGetCloudConversations.mockReset();
    getHomeMock.mockReset();
    getHomeMock.mockResolvedValue({ home: "/Users/test" });
    getConversationMock.mockReset();
    getConversationMock.mockResolvedValue({ workspace: {} });
  });

  // @spec WUP-001 — Default-fallback relative working dirs are resolved
  // against /api/file/home, not the filesystem root.
  it("uploads local conversations under the agent-server home dir when working dir is relative", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });

    const result = await uploadFilesToConversation("conv-1", [
      makeFile("a.txt"),
    ]);

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "a.txt" }),
      "/Users/test/workspace/project/a.txt",
    );
    expect(result.uploaded_files).toEqual(["a.txt"]);
    expect(batchGetCloudConversations).not.toHaveBeenCalled();
    expect(getHomeMock).toHaveBeenCalled();
  });

  // @spec WUP-001 — Absolute working dirs (e.g. the conversation's own
  // `workspace.working_dir`) pass through without a /api/file/home round-trip.
  it("respects an absolute conversation working_dir verbatim", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });

    const result = await uploadFilesToConversation(
      "conv-1",
      [makeFile("notes.md")],
      {
        id: "conv-1",
        workspace: { working_dir: "/Users/test/projects/foo" },
      } as never,
    );

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "notes.md" }),
      "/Users/test/projects/foo/notes.md",
    );
    expect(result.uploaded_files).toEqual(["notes.md"]);
    expect(getHomeMock).not.toHaveBeenCalled();
  });

  it("uploads cloud conversations against the provisioned runtime URL", async () => {
    setRegisteredBackends([cloudBackend]);
    setActiveSelection({ backendId: cloudBackend.id });
    batchGetCloudConversations.mockResolvedValue([
      {
        id: "1717df59-63ee-43bf-b32a-83428d3efdc8",
        conversation_url:
          "http://runtime.example.dev/api/conversations/1717df59-63ee-43bf-b32a-83428d3efdc8",
        session_api_key: "runtime-session-key",
        workspace: { working_dir: "/workspace/project" },
      },
    ]);

    const conversationId = "1717df59-63ee-43bf-b32a-83428d3efdc8";
    const result = await uploadFilesToConversation(conversationId, [
      makeFile("notes.md"),
    ]);

    expect(batchGetCloudConversations).toHaveBeenCalledWith([conversationId]);
    expect(RemoteWorkspace).toHaveBeenCalledWith(
      expect.objectContaining({
        host: "http://runtime.example.dev",
        apiKey: "runtime-session-key",
      }),
    );
    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "notes.md" }),
      "/workspace/project/notes.md",
    );
    expect(result.uploaded_files).toEqual(["notes.md"]);
  });

  // @spec WUP-002 — the runtime-reported working dir wins over a divergent
  // locally-derived value (here a stale attached workspace), so the destination
  // stays inside the workspace the agent-server actually stored.
  it("anchors the upload to the runtime-reported working dir over a divergent local value", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });
    getConversationMock.mockResolvedValue({
      workspace: { working_dir: "/workspace/project/OpenHands" },
    });

    const result = await uploadFilesToConversation(
      "conv-1",
      [makeFile("archive.zip")],
      {
        id: "conv-1",
        workspace: { working_dir: "/stale/wrong/workspace" },
      } as never,
    );

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "archive.zip" }),
      "/workspace/project/OpenHands/archive.zip",
    );
    expect(result.uploaded_files).toEqual(["archive.zip"]);
  });

  // @spec WUP-002 — a runtime read that reports no working dir keeps the
  // WUP-001 home-anchored fallback.
  it("falls back to the home-anchored dir when the runtime reports no working dir", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });
    getConversationMock.mockResolvedValue({ workspace: {} });

    await uploadFilesToConversation("conv-1", [makeFile("a.txt")]);

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "a.txt" }),
      "/Users/test/workspace/project/a.txt",
    );
  });

  // @spec WUP-002 — a runtime that reports a *relative* working dir is not
  // authoritative (the guard resolves it against the server CWD, which Canvas
  // cannot know), so the local resolution still wins.
  it("ignores a relative runtime working dir and keeps the local resolution", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });
    getConversationMock.mockResolvedValue({
      workspace: { working_dir: "workspace/project/abc123" },
    });

    await uploadFilesToConversation("conv-1", [makeFile("a.txt")]);

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "a.txt" }),
      "/Users/test/workspace/project/a.txt",
    );
  });

  // @spec WUP-002 — a failed runtime read must not break the upload.
  it("falls back to the local resolution when the runtime read fails", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });
    getConversationMock.mockRejectedValue(new Error("runtime unavailable"));

    const result = await uploadFilesToConversation("conv-1", [
      makeFile("a.txt"),
    ]);

    expect(fileUploadMock).toHaveBeenCalledWith(
      expect.objectContaining({ name: "a.txt" }),
      "/Users/test/workspace/project/a.txt",
    );
    expect(result.uploaded_files).toEqual(["a.txt"]);
  });

  // @spec WUP-002 — a guard rejection surfaces a human-readable reason instead
  // of the raw 422 JSON body.
  it("maps a workspace-guard 422 to a friendly skipped-file reason", async () => {
    setRegisteredBackends([
      {
        id: "local-1",
        name: "Local",
        host: "http://127.0.0.1:18000",
        apiKey: "local-key",
        kind: "local",
      },
    ]);
    setActiveSelection({ backendId: "local-1" });
    fileUploadMock.mockRejectedValue(
      new HttpError(422, "Unprocessable Entity", {
        detail: "path must be inside the conversation workspace",
      }),
    );

    const result = await uploadFilesToConversation("conv-1", [
      makeFile("archive.zip"),
    ]);

    expect(result.uploaded_files).toEqual([]);
    expect(result.skipped_files).toEqual([
      {
        name: "archive.zip",
        reason: I18nKey.FILE_SERVICE$UPLOAD_WORKSPACE_MISMATCH,
      },
    ]);
  });
});
