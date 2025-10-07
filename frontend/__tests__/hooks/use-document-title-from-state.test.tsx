import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useDocumentTitleFromState } from "#/hooks/use-document-title-from-state";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

// Mock the useActiveConversation hook
vi.mock("#/hooks/query/use-active-conversation");

const mockUseActiveConversation = vi.mocked(useActiveConversation);

describe("useDocumentTitleFromState", () => {
  const originalTitle = document.title;

  beforeEach(() => {
    vi.clearAllMocks();
    document.title = "Test";
  });

  afterEach(() => {
    document.title = originalTitle;
    vi.resetAllMocks();
  });

  it("should set document title to default suffix when no conversation", () => {
    mockUseActiveConversation.mockReturnValue({
      data: null,
    } as any);

    renderHook(() => useDocumentTitleFromState());

    expect(document.title).toBe("OpenHands");
  });

  it("should set document title to custom suffix when no conversation", () => {
    mockUseActiveConversation.mockReturnValue({
      data: null,
    } as any);

    renderHook(() => useDocumentTitleFromState("Custom App"));

    expect(document.title).toBe("Custom App");
  });

  it("should set document title with conversation title", () => {
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: "My Conversation",
        status: "RUNNING",
      },
    } as any);

    renderHook(() => useDocumentTitleFromState());

    expect(document.title).toBe("My Conversation | OpenHands");
  });

  it("should update document title when conversation title changes", () => {
    // Initial state - no conversation
    mockUseActiveConversation.mockReturnValue({
      data: null,
    } as any);

    const { rerender } = renderHook(() => useDocumentTitleFromState());
    expect(document.title).toBe("OpenHands");

    // Conversation with initial title
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: "Conversation 65e29",
        status: "RUNNING",
      },
    } as any);
    rerender();
    expect(document.title).toBe("Conversation 65e29 | OpenHands");

    // Conversation title updated to human-readable title
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: "Help me build a React app",
        status: "RUNNING",
      },
    } as any);
    rerender();
    expect(document.title).toBe("Help me build a React app | OpenHands");
  });

  it("should handle conversation without title", () => {
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: undefined,
        status: "RUNNING",
      },
    } as any);

    renderHook(() => useDocumentTitleFromState());

    expect(document.title).toBe("OpenHands");
  });

  it("should handle empty conversation title", () => {
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: "",
        status: "RUNNING",
      },
    } as any);

    renderHook(() => useDocumentTitleFromState());

    expect(document.title).toBe("OpenHands");
  });

  it("should reset document title on cleanup", () => {
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_id: "123",
        title: "My Conversation",
        status: "RUNNING",
      },
    } as any);

    const { unmount } = renderHook(() => useDocumentTitleFromState());

    expect(document.title).toBe("My Conversation | OpenHands");

    unmount();

    expect(document.title).toBe("OpenHands");
  });
});
