import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FileContentViewer } from "#/components/features/files-tab/file-content-viewer";
import type { ViewMode } from "#/components/features/files-tab/view-mode";
import { useWorkspaceMutationCounter } from "#/stores/use-workspace-mutation-counter";

// Mock the *services* the file-content hook depends on — not the hook itself —
// so the real classification (text decoded, then flipped to binary on a NUL
// sniff) runs end to end through the viewer.
const useWorkspaceSessionMock = vi.fn();
vi.mock("#/hooks/query/use-workspace-session", async (importOriginal) => {
  const real =
    await importOriginal<
      typeof import("#/hooks/query/use-workspace-session")
    >();
  return {
    ...real, // keep the real joinWorkspaceUrl the hook builds its fetch URL with
    useWorkspaceSession: () => useWorkspaceSessionMock(),
  };
});

const useActiveConversationMock = vi.fn();
vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: () => useActiveConversationMock(),
}));

const useRuntimeIsReadyMock = vi.fn();
vi.mock("#/hooks/use-runtime-is-ready", () => ({
  useRuntimeIsReady: () => useRuntimeIsReadyMock(),
}));

const getActiveBackendMock = vi.fn();
vi.mock("#/api/backend-registry/active-store", () => ({
  getActiveBackend: () => getActiveBackendMock(),
}));

vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({
    t: (key: string, values?: { path?: string }) =>
      `${key} ${values?.path ?? ""}`,
  }),
}));

const downloadFileMock = vi.fn();
vi.mock("#/api/runtime-service/agent-server-runtime-service", () => ({
  default: { downloadFile: (...args: unknown[]) => downloadFileMock(...args) },
}));

const fetchMock = vi.fn();

const BASE_URL =
  "https://agent.example.com/api/conversations/conv-1/workspace/";

function renderViewer(path: string, viewMode: ViewMode = "rich") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <FileContentViewer path={path} viewMode={viewMode} />
    </QueryClientProvider>,
  );
}

describe("FileContentViewer", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
    downloadFileMock.mockReset();
    useWorkspaceSessionMock.mockReset();
    useActiveConversationMock.mockReset();
    useRuntimeIsReadyMock.mockReset();
    getActiveBackendMock.mockReset();

    useRuntimeIsReadyMock.mockReturnValue(true);
    useActiveConversationMock.mockReturnValue({
      data: {
        id: "conv-1",
        conversation_url: "https://agent.example.com/api/conversations/conv-1",
        session_api_key: "session-key",
      },
    });
    useWorkspaceSessionMock.mockReturnValue({
      data: { baseUrl: BASE_URL },
      isLoading: false,
      isError: false,
      error: null,
    });
    getActiveBackendMock.mockReturnValue({
      backend: { id: "local-1", kind: "local", host: "http://localhost:8000" },
      orgId: null,
    });
    useWorkspaceMutationCounter.setState({ count: 0 });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // The acceptance criteria require the clear message in BOTH view modes. The
  // plain-mode fallback and the rich-mode binary branch both route through
  // UnpreviewableFallback, so one parametrized spec covers both code paths.
  it.each(["rich", "plain"] as const)(
    "shows a clear unsupported-document message for an Office file (.pptx) in %s mode",
    async (viewMode) => {
      // Arrange: the workspace fileserver returns real .pptx bytes — a ZIP whose
      // header carries a NUL, so the hook classifies the file as binary.
      fetchMock.mockResolvedValue({
        ok: true,
        status: 200,
        arrayBuffer: () =>
          Promise.resolve(
            new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0x00]).buffer,
          ),
      });

      // Act
      renderViewer("demo.pptx", viewMode);

      // Assert: the format-aware "no preview" message replaces the generic
      // binary fallback in both modes, so the pane is never blank.
      expect(
        await screen.findByTestId("file-content-viewer-unsupported-document"),
      ).toBeInTheDocument();
    },
  );

  it.each(["html", "md"])(
    "explains why an absolute %s cannot load sibling assets instead of a broken rich preview",
    async (extension) => {
      const path = `/outside/report.${extension}`;
      const source = "<p>Report with sibling assets</p>";
      downloadFileMock.mockResolvedValue(
        new TextEncoder().encode(source).buffer,
      );
      renderViewer(path);
      expect(
        await screen.findByTestId("file-content-viewer-relative-assets"),
      ).toHaveTextContent(path);
      expect(
        screen.queryByTestId("file-content-viewer-iframe"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("file-content-viewer-markdown"),
      ).not.toBeInTheDocument();
    },
  );

  it.each(["html", "md"])(
    "keeps the absolute %s source available in Plain",
    async (extension) => {
      downloadFileMock.mockResolvedValue(
        new TextEncoder().encode("Report source").buffer,
      );
      renderViewer(`/outside/report.${extension}`, "plain");
      expect(
        await screen.findByTestId("file-content-viewer-highlighted"),
      ).toHaveTextContent("Report source");
      expect(
        screen.queryByTestId("file-content-viewer-relative-assets"),
      ).not.toBeInTheDocument();
    },
  );

  it("names the absolute file when its download loses the connection", async () => {
    downloadFileMock.mockRejectedValue(new TypeError("Failed to fetch"));
    renderViewer("/outside/chart.png");
    const error = await screen.findByTestId("file-content-viewer-error");
    expect(error).toHaveTextContent("/outside/chart.png");
    expect(error).toHaveTextContent("Disconnected");
  });

  it("replaces an undecodable image with a named error instead of a broken icon", async () => {
    downloadFileMock.mockResolvedValue(
      new TextEncoder().encode("not an image").buffer,
    );
    renderViewer("/outside/broken.png");
    const img = await screen.findByRole("img", { name: "/outside/broken.png" });
    fireEvent.error(img);
    expect(
      await screen.findByTestId("file-content-viewer-image-error"),
    ).toHaveTextContent("/outside/broken.png");
    expect(
      screen.queryByRole("img", { name: "/outside/broken.png" }),
    ).not.toBeInTheDocument();
  });
});
