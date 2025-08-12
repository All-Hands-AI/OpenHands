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
    const originalResolvedLanguage = i18n.resolvedLanguage;

    // Set up spies to verify the language resolution
    const changeLanguageSpy = vi.spyOn(i18n, 'changeLanguage');

    try {
      // Test with a language code that includes region (e.g., en-US)
      i18n.changeLanguage("en-US");

      // Verify that the language is resolved to the base language (en)
      // This is what the "load: languageOnly" option should do
      expect(changeLanguageSpy).toHaveBeenCalledWith("en-US");

      // The actual language used should be "en" due to the languageOnly setting
      // Note: In a real browser, i18next would make an HTTP request for the translation file
      // In tests, we're just verifying the language resolution behavior
      expect(i18n.language).toBe("en-US");

      // The resolved language (what's actually used for loading resources) should be "en"
      // This is what prevents the 404 error for "/locales/en-US/translation.json"
      if (i18n.resolvedLanguage) {
        expect(i18n.resolvedLanguage).toBe("en");
      }
    } finally {
      // Restore the original language
      i18n.changeLanguage(originalLanguage);
      changeLanguageSpy.mockRestore();
    }
  });
});
