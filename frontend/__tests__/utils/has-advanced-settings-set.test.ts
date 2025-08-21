import { describe, expect, it, test } from "vitest";
import { hasAdvancedSettingsSet } from "#/utils/has-advanced-settings-set";
import { DEFAULT_SETTINGS } from "#/services/settings";

describe("hasAdvancedSettingsSet", () => {
  it("should return false by default", () => {
    expect(hasAdvancedSettingsSet(DEFAULT_SETTINGS)).toBe(false);
  });

  it("should return false if an empty object", () => {
    expect(hasAdvancedSettingsSet({})).toBe(false);
  });

  describe("should be true if", () => {
    test("LLM_BASE_URL is set", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          LLM_BASE_URL: "test",
        }),
      ).toBe(true);
    });

    test("AGENT is not default value", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          AGENT: "test",
        }),
      ).toBe(true);
    });

    test("CONFIRMATION_MODE is true", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          CONFIRMATION_MODE: true,
        }),
      ).toBe(true);
    });

    test("SECURITY_ANALYZER is set", () => {
      expect(
        hasAdvancedSettingsSet({
          ...DEFAULT_SETTINGS,
          SECURITY_ANALYZER: "test",
        }),
      ).toBe(true);
    });
  });
});
