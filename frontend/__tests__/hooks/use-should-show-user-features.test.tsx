import { renderHook } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { useShouldShowUserFeatures } from "#/hooks/use-should-show-user-features";
import { useConfig } from "#/hooks/query/use-config";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useUserProviders } from "#/hooks/use-user-providers";
import { getLoginMethod, LoginMethod } from "#/utils/local-storage";

// Mock the dependencies
vi.mock("#/hooks/query/use-config");
vi.mock("#/hooks/query/use-is-authed");
vi.mock("#/hooks/use-user-providers");
vi.mock("#/utils/local-storage");

const mockUseConfig = vi.mocked(useConfig);
const mockUseIsAuthed = vi.mocked(useIsAuthed);
const mockUseUserProviders = vi.mocked(useUserProviders);
const mockGetLoginMethod = vi.mocked(getLoginMethod);

describe("useShouldShowUserFeatures", () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should return false when config is not loaded", () => {
    mockUseConfig.mockReturnValue({ data: null } as any);
    mockUseIsAuthed.mockReturnValue({ data: false } as any);
    mockUseUserProviders.mockReturnValue({ providers: [] } as any);
    mockGetLoginMethod.mockReturnValue(null);

    const { result } = renderHook(() => useShouldShowUserFeatures());

    expect(result.current).toBe(false);
  });

  describe("SAAS mode", () => {
    it("should return true when authenticated", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "saas" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: true } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(null);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(true);
    });

    it("should return true when not authenticated but has login method stored", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "saas" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: false } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(LoginMethod.GITHUB);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(true);
    });

    it("should return false when not authenticated and no login method stored", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "saas" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: false } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(null);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(false);
    });
  });

  describe("OSS mode", () => {
    it("should return true when authenticated and has providers", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "oss" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: true } as any);
      mockUseUserProviders.mockReturnValue({ providers: ["github"] } as any);
      mockGetLoginMethod.mockReturnValue(null);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(true);
    });

    it("should return false when authenticated but no providers", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "oss" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: true } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(null);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(false);
    });

    it("should return false when not authenticated even with login method stored", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "oss" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: false } as any);
      mockUseUserProviders.mockReturnValue({ providers: ["github"] } as any);
      mockGetLoginMethod.mockReturnValue(LoginMethod.GITHUB);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(false);
    });
  });

  describe("Other modes", () => {
    it("should return true when authenticated", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "other" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: true } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(null);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(true);
    });

    it("should return false when not authenticated", () => {
      mockUseConfig.mockReturnValue({ data: { APP_MODE: "other" } } as any);
      mockUseIsAuthed.mockReturnValue({ data: false } as any);
      mockUseUserProviders.mockReturnValue({ providers: [] } as any);
      mockGetLoginMethod.mockReturnValue(LoginMethod.GITHUB);

      const { result } = renderHook(() => useShouldShowUserFeatures());

      expect(result.current).toBe(false);
    });
  });
});
