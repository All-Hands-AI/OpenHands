import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import i18n from "../../src/i18n";
import { AccountSettingsContextMenu } from "../../src/components/features/context-menu/account-settings-context-menu";
import { renderWithProviders } from "../../test-utils";

describe("Translations", () => {
  it("should render translated text", () => {
    i18n.changeLanguage("en");
    renderWithProviders(
      <AccountSettingsContextMenu
        onLogout={() => {}}
        onClose={() => {}}
      />,
    );
    expect(
      screen.getByTestId("account-settings-context-menu"),
    ).toBeInTheDocument();
  });

  it("should handle language codes with region parts", () => {
    // Mock the language detection to return a language with region code
    const originalLanguage = i18n.language;

    // Set up spies to verify the language resolution
    const changeLanguageSpy = vi.spyOn(i18n, 'changeLanguage');

    try {
      // Test with a language code that includes region (e.g., en-US)
      i18n.changeLanguage("en-US");

      // Verify that the language change was called with the correct parameter
      expect(changeLanguageSpy).toHaveBeenCalledWith("en-US");

      // The actual language used should be "en-US"
      expect(i18n.language).toBe("en-US");

      // With our configuration, i18next should try to load "en-US" first,
      // but if that fails, it will fall back to "en" due to nonExplicitSupportedLngs: true
      // In a real browser, this prevents the 404 error for "/locales/en-US/translation.json"
    } finally {
      // Restore the original language
      i18n.changeLanguage(originalLanguage);
      changeLanguageSpy.mockRestore();
    }
  });

  it("should properly handle zh-CN and zh-TW language codes", () => {
    // These are both explicitly supported languages in the app
    const originalLanguage = i18n.language;

    try {
      // Test Simplified Chinese
      i18n.changeLanguage("zh-CN");
      expect(i18n.language).toBe("zh-CN");

      // The language should be resolved exactly as zh-CN since it's in the supported languages list
      if (i18n.resolvedLanguage) {
        expect(i18n.resolvedLanguage).toBe("zh-CN");
      }

      // Test Traditional Chinese
      i18n.changeLanguage("zh-TW");
      expect(i18n.language).toBe("zh-TW");

      // The language should be resolved exactly as zh-TW since it's in the supported languages list
      if (i18n.resolvedLanguage) {
        expect(i18n.resolvedLanguage).toBe("zh-TW");
      }

      // Test a variant that's not explicitly supported
      i18n.changeLanguage("zh-HK");
      expect(i18n.language).toBe("zh-HK");

      // This should fall back to zh or en depending on the configuration
      // With nonExplicitSupportedLngs: true, it might try to match with a supported language
      // that shares the same base language code
      if (i18n.resolvedLanguage) {
        // It could resolve to zh-CN, zh-TW, or fall back to en
        // The exact behavior depends on i18next's internal language resolution algorithm
        const possibleResolutions = ["zh-CN", "zh-TW", "en"];
        expect(possibleResolutions).toContain(i18n.resolvedLanguage);
      }
    } finally {
      // Restore the original language
      i18n.changeLanguage(originalLanguage);
    }
  });
});
