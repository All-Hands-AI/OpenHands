import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SettingsService from "#/api/settings-service/settings-service.api";
import { useSettingsDocumentSchema } from "#/hooks/query/use-settings-document";

vi.mock("#/api/settings-service/settings-service.api", () => ({
  default: {
    getSettingsDocumentSchema: vi.fn(),
  },
}));

vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => ({ data: true }),
}));

vi.mock("#/contexts/active-backend-context", () => ({
  useActiveBackend: () => ({
    backend: { id: "local", kind: "local", host: "http://localhost:3000" },
    orgId: null,
  }),
}));

vi.mock("#/api/backend-registry/active-store", () => ({
  isNoBackend: () => false,
}));

describe("useSettingsDocumentSchema", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.useFakeTimers();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.mocked(SettingsService.getSettingsDocumentSchema).mockResolvedValue({
      model_name: "SettingsDocument",
      sections: [],
    });
  });

  afterEach(() => {
    queryClient.clear();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("polls the canonical schema for newly registered fields", async () => {
    renderHook(() => useSettingsDocumentSchema(), { wrapper });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(SettingsService.getSettingsDocumentSchema).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(SettingsService.getSettingsDocumentSchema).toHaveBeenCalledTimes(2);
  });
});
