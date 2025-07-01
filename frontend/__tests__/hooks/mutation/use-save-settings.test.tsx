import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";

// Mock the useSettings hook
vi.mock("#/hooks/query/use-settings", () => ({
  useSettings: () => ({
    data: {},
  }),
}));

describe("useSaveSettings", () => {
  let saveSettingsSpy: any;
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient();
    saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings").mockResolvedValue(true);
  });

  it("should send an empty string for llm_api_key if an empty string is passed, otherwise undefined", async () => {
    const { result } = renderHook(() => useSaveSettings(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    result.current.mutate({ llm_api_key: "" });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: "",
        }),
      );
    });

    saveSettingsSpy.mockClear();
    result.current.mutate({ llm_api_key: null });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: undefined,
        }),
      );
    });
  });

  it("should only include search_api_key in the request when explicitly provided", async () => {
    const { result } = renderHook(() => useSaveSettings(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    // When SEARCH_API_KEY is provided, it should be included in the request
    result.current.mutate({ SEARCH_API_KEY: "test-api-key" });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          search_api_key: "test-api-key",
        }),
      );
    });

    // When SEARCH_API_KEY is not provided, it should not be included in the request
    saveSettingsSpy.mockClear();
    result.current.mutate({ LLM_MODEL: "test-model" });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalled();
      const callArg = saveSettingsSpy.mock.calls[0][0];
      expect(callArg.search_api_key).toBeUndefined();
    });
  });
});
