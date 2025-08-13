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

  it("should handle language codes with region parts", async () => {
    // Test that the configuration properly handles language codes with regions
    const originalLanguage = i18n.language;

    try {
      // Test with a language code that includes region (e.g., en-US)
      await i18n.changeLanguage("en-US");
      expect(i18n.language).toBe("en-US");

      // With nonExplicitSupportedLngs: true, unsupported region codes should fall back
      // to base languages that are in the supportedLngs list
    } finally {
      // Restore the original language
      await i18n.changeLanguage(originalLanguage);
    }
  });

  it("should have proper i18n configuration", () => {
    // Test that the i18n instance has the expected configuration
    expect(i18n.options.supportedLngs).toBeDefined();
    expect(i18n.options.nonExplicitSupportedLngs).toBe(true);

    // fallbackLng can be a string or array, check if it includes "en"
    const fallbackLng = i18n.options.fallbackLng;
    if (Array.isArray(fallbackLng)) {
      expect(fallbackLng).toContain("en");
    } else {
      expect(fallbackLng).toBe("en");
    }

    // Test that supported languages include both base and region-specific codes
    const supportedLngs = i18n.options.supportedLngs as string[];
    expect(supportedLngs).toContain("en");
    expect(supportedLngs).toContain("zh-CN");
    expect(supportedLngs).toContain("zh-TW");
    expect(supportedLngs).toContain("ko-KR");
  });
});
