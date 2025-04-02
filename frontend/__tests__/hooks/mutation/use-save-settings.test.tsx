import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { AuthProvider } from "#/context/auth-context";

describe("useSaveSettings", () => {
  it("should send an empty string for llm_api_key if an empty string is passed, otherwise undefined", async () => {
    const saveSettingsSpy = vi.spyOn(OpenHands, "saveSettings");
    const { result } = renderHook(() => useSaveSettings(), {
      wrapper: ({ children }) => (
        <AuthProvider>
          <QueryClientProvider client={new QueryClient()}>
            {children}
          </QueryClientProvider>
        </AuthProvider>
      ),
    });

    result.current.mutate({ LLM_API_KEY: "" });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: "",
        }),
      );
    });

    result.current.mutate({ LLM_API_KEY: null });
    await waitFor(() => {
      expect(saveSettingsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          llm_api_key: undefined,
        }),
      );
    });
  });
});
