import { describe, expect, it, test } from "vitest";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { DEFAULT_SETTINGS } from "#/services/settings";

describe("hasAdvancedSettingsSet", () => {
  it("should return false by default", () => {
    expect(hasAdvancedSettingsSet(DEFAULT_SETTINGS)).toBe(false);
  });

  describe("should be true if", () => {
    test("LLM_BASE_URL is set", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          llm_base_url: "test",
        }),
      ).toBe(true);
    });

    test("AGENT is not default value", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          agent: "test",
        }),
      ).toBe(true);
    });

    test("REMOTE_RUNTIME_RESOURCE_FACTOR is not default value", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          remote_runtime_resource_factor: 999,
        }),
      ).toBe(true);
    });

    test("CONFIRMATION_MODE is true", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          confirmation_mode: true,
        }),
      ).toBe(true);
    });

    test("SECURITY_ANALYZER is set", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          security_analyzer: "test",
        }),
      ).toBe(true);
    });
  });
});
