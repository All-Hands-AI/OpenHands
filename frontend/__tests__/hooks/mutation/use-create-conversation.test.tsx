import { renderHook, act } from "@testing-library/react";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import OpenHands from "#/api/open-hands";
import { useNavigate } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock dependencies
vi.mock("react-router", () => ({
  useNavigate: vi.fn(),
}));

vi.mock("react-redux", () => ({
  useDispatch: vi.fn(),
  useSelector: vi.fn(),
}));

vi.mock("#/api/open-hands", () => ({
  default: {
    createConversation: vi.fn(),
  },
}));

vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

describe("useCreateConversation", () => {
  const mockNavigate = vi.fn();
  const mockDispatch = vi.fn();
  const mockQueryClient = new QueryClient();
  
  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as any).mockReturnValue(mockNavigate);
    (useDispatch as any).mockReturnValue(mockDispatch);
    (useSelector as any).mockReturnValue({
      selectedRepository: null,
      files: [],
      replayJson: null,
    });
    (OpenHands.createConversation as any).mockResolvedValue({
      conversation_id: "test-id",
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={mockQueryClient}>{children}</QueryClientProvider>
  );

  it("should throw an error when no query, repository, files, or replayJson is provided", async () => {
    const { result } = renderHook(() => useCreateConversation(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync({ q: "" })).rejects.toThrow(
        "No query provided"
      );
    });
  });

  it("should allow empty query when allowEmptyQuery is true", async () => {
    const { result } = renderHook(() => useCreateConversation(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ q: "", allowEmptyQuery: true });
    });

    expect(OpenHands.createConversation).toHaveBeenCalledWith(
      undefined,
      "",
      [],
      undefined
    );
    expect(mockNavigate).toHaveBeenCalledWith("/conversations/test-id");
  });
});