import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual("@tanstack/react-query");
  return {
    ...actual,
    useQuery: vi.fn(),
    useQueries: vi.fn(),
  };
});

// Mock the dependencies
vi.mock("#/hooks/use-conversation-id", () => ({
  useConversationId: () => ({ conversationId: "test-conversation-id" }),
}));

vi.mock("#/hooks/use-runtime-is-ready", () => ({
  useRuntimeIsReady: () => true,
}));

vi.mock("#/api/open-hands", () => ({
  default: {
    getWebHosts: vi
      .fn()
      .mockResolvedValue(["http://localhost:3000", "http://localhost:3001"]),
  },
}));

vi.mock("axios", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: "OK" }),
    create: vi.fn(() => ({
      get: vi.fn(),
      interceptors: {
        response: {
          use: vi.fn(),
        },
      },
    })),
  },
}));

describe("useActiveHost", () => {
  let queryClient: QueryClient;

  beforeEach(async () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // Mock useQuery to return hosts data
    const { useQuery, useQueries } = await import("@tanstack/react-query");
    vi.mocked(useQuery).mockReturnValue({
      data: { hosts: ["http://localhost:3000", "http://localhost:3001"] },
      isLoading: false,
      error: null,
    } as any);

    // Mock useQueries to return empty array of results
    vi.mocked(useQueries).mockReturnValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should configure refetchInterval for host availability queries", async () => {
    // Import the hook after mocks are set up
    const { useActiveHost } = await import("#/hooks/query/use-active-host");
    const { useQueries } = await import("@tanstack/react-query");

    renderHook(() => useActiveHost(), { wrapper });

    // Check that useQueries was called
    expect(useQueries).toHaveBeenCalled();

    // Get the queries configuration passed to useQueries
    const queriesConfig = vi.mocked(useQueries).mock.calls[0][0];

    // Verify that the queries configuration includes refetchInterval
    expect(queriesConfig).toEqual({
      queries: expect.arrayContaining([
        expect.objectContaining({
          refetchInterval: 3000,
        }),
      ]),
    });
  });

  it("should fail if refetchInterval is not configured", async () => {
    // Import the hook after mocks are set up
    const { useActiveHost } = await import("#/hooks/query/use-active-host");
    const { useQueries } = await import("@tanstack/react-query");

    renderHook(() => useActiveHost(), { wrapper });

    // Check that useQueries was called
    expect(useQueries).toHaveBeenCalled();

    // Get the queries configuration passed to useQueries
    const queriesConfig = vi.mocked(useQueries).mock.calls[0][0];

    // This test will fail if refetchInterval is commented out in the hook
    // because the queries won't have the refetchInterval property
    const hasRefetchInterval = (queriesConfig as any).queries.some(
      (query: any) => query.refetchInterval === 3000,
    );

    expect(hasRefetchInterval).toBe(true);
  });
});
