import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useFeedbackExists } from "#/hooks/query/use-feedback-exists";

// Mock the useConfig hook
vi.mock("#/hooks/query/use-config", () => ({
  useConfig: vi.fn(),
}));

// Mock the useConversationId hook
vi.mock("#/hooks/use-conversation-id", () => ({
  useConversationId: () => ({ conversationId: "test-conversation-id" }),
}));

describe("useFeedbackExists", () => {
  let queryClient: QueryClient;
  const mockCheckFeedbackExists = vi.spyOn(OpenHands, "checkFeedbackExists");

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    mockCheckFeedbackExists.mockClear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should not call API when APP_MODE is not saas", async () => {
    const { useConfig } = await import("#/hooks/query/use-config");
    vi.mocked(useConfig).mockReturnValue({
      data: { APP_MODE: "oss" },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConfig>);

    const { result } = renderHook(() => useFeedbackExists(123), {
      wrapper,
    });

    // Wait for any potential async operations
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify that the API was not called
    expect(mockCheckFeedbackExists).not.toHaveBeenCalled();

    // Verify that the query is disabled
    expect(result.current.data).toBeUndefined();
  });

  it("should call API when APP_MODE is saas", async () => {
    const { useConfig } = await import("#/hooks/query/use-config");
    vi.mocked(useConfig).mockReturnValue({
      data: { APP_MODE: "saas" },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConfig>);

    mockCheckFeedbackExists.mockResolvedValue({
      exists: true,
      rating: 5,
      reason: "Great job!",
    });

    const { result } = renderHook(() => useFeedbackExists(123), {
      wrapper,
    });

    // Wait for the query to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify that the API was called
    expect(mockCheckFeedbackExists).toHaveBeenCalledWith(
      "test-conversation-id",
      123,
    );

    // Verify that the data is returned
    expect(result.current.data).toEqual({
      exists: true,
      rating: 5,
      reason: "Great job!",
    });
  });

  it("should not call API when eventId is not provided", async () => {
    const { useConfig } = await import("#/hooks/query/use-config");
    vi.mocked(useConfig).mockReturnValue({
      data: { APP_MODE: "saas" },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useConfig>);

    const { result } = renderHook(() => useFeedbackExists(undefined), {
      wrapper,
    });

    // Wait for any potential async operations
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify that the API was not called
    expect(mockCheckFeedbackExists).not.toHaveBeenCalled();

    // Verify that the query is disabled
    expect(result.current.data).toBeUndefined();
  });

  it("should not call API when config is not loaded yet", async () => {
    const { useConfig } = await import("#/hooks/query/use-config");
    vi.mocked(useConfig).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useConfig>);

    const { result } = renderHook(() => useFeedbackExists(123), {
      wrapper,
    });

    // Wait for any potential async operations
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify that the API was not called
    expect(mockCheckFeedbackExists).not.toHaveBeenCalled();

    // Verify that the query is disabled
    expect(result.current.data).toBeUndefined();
  });
});
