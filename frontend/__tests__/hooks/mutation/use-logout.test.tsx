import { renderHook, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { useLogout } from "#/hooks/mutation/use-logout";
import { useConfig } from "#/hooks/query/use-config";
import OpenHands from "#/api/open-hands";
import { clearLoginData } from "#/utils/local-storage";

// Mock the dependencies
vi.mock("#/hooks/query/use-config");
vi.mock("#/api/open-hands");
vi.mock("#/utils/local-storage");
vi.mock("posthog-js", () => ({
  default: {
    reset: vi.fn(),
  },
}));

// Mock window.location.reload
Object.defineProperty(window, "location", {
  value: {
    reload: vi.fn(),
  },
  writable: true,
});

const mockUseConfig = vi.mocked(useConfig);
const mockOpenHands = vi.mocked(OpenHands);
const mockClearLoginData = vi.mocked(clearLoginData);

// Create a wrapper component for React Query
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useLogout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseConfig.mockReturnValue({ data: { APP_MODE: "saas" } } as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should perform client-side cleanup on successful logout", async () => {
    mockOpenHands.logout = vi.fn().mockResolvedValue(undefined);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockOpenHands.logout).toHaveBeenCalledWith("saas");
    expect(mockClearLoginData).toHaveBeenCalled();
    expect(window.location.reload).toHaveBeenCalled();
  });

  it("should perform client-side cleanup even when logout API fails with 401", async () => {
    const error = new Error("Unauthorized");
    (error as any).response = { status: 401 };
    mockOpenHands.logout = vi.fn().mockRejectedValue(error);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(mockOpenHands.logout).toHaveBeenCalledWith("saas");
    expect(mockClearLoginData).toHaveBeenCalled();
    expect(window.location.reload).toHaveBeenCalled();
  });

  it("should perform client-side cleanup even when logout API fails with other errors", async () => {
    const error = new Error("Network error");
    mockOpenHands.logout = vi.fn().mockRejectedValue(error);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(mockOpenHands.logout).toHaveBeenCalledWith("saas");
    expect(mockClearLoginData).toHaveBeenCalled();
    expect(window.location.reload).toHaveBeenCalled();
  });

  it("should not clear login data in OSS mode", async () => {
    mockUseConfig.mockReturnValue({ data: { APP_MODE: "oss" } } as any);
    mockOpenHands.logout = vi.fn().mockResolvedValue(undefined);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockOpenHands.logout).toHaveBeenCalledWith("oss");
    expect(mockClearLoginData).not.toHaveBeenCalled();
    expect(window.location.reload).toHaveBeenCalled();
  });
});
