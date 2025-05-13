import { describe, expect, it } from "vitest";
import translationJson from "../../src/i18n/translation.json";
import { AvailableLanguages } from "../../src/i18n";

describe("Translation Completeness", () => {
  it("should have all translation keys available in all supported languages", () => {
    // Get all supported language codes from AvailableLanguages
    const supportedLanguageCodes = AvailableLanguages.map((lang) => lang.value);
    
    // Track missing translations
    const missingTranslations: Record<string, string[]> = {};
    
    // Check each translation key
    Object.entries(translationJson).forEach(([key, translations]) => {
      // Get the languages available for this key
      const availableLanguages = Object.keys(translations as Record<string, string>);
      
      // Find missing languages for this key
      const missing = supportedLanguageCodes.filter(
        (langCode) => !availableLanguages.includes(langCode)
      );
      
      if (missing.length > 0) {
        missingTranslations[key] = missing;
      }
    });
    
    // Generate detailed error message if there are missing translations
    if (Object.keys(missingTranslations).length > 0) {
      const errorDetails = Object.entries(missingTranslations)
        .map(([key, langs]) => `- Key "${key}" is missing translations for: ${langs.join(", ")}`)
        .join("\n");
      
      const errorMessage = `Found ${Object.keys(missingTranslations).length} translation keys with missing languages:\n${errorDetails}`;
      console.error(errorMessage);
      expect(Object.keys(missingTranslations).length).toBe(0, errorMessage);
    }
  });

  it("should not have extra languages that are not in AvailableLanguages", () => {
    // Get all supported language codes from AvailableLanguages
    const supportedLanguageCodes = AvailableLanguages.map((lang) => lang.value);
    
    // Track extra languages
    const extraLanguages: Record<string, string[]> = {};
    
    // Check each translation key
    Object.entries(translationJson).forEach(([key, translations]) => {
      // Get the languages available for this key
      const availableLanguages = Object.keys(translations as Record<string, string>);
      
      // Find extra languages for this key
      const extra = availableLanguages.filter(
        (langCode) => !supportedLanguageCodes.includes(langCode)
      );
      
      if (extra.length > 0) {
        extraLanguages[key] = extra;
      }
    });
    
    // Generate detailed error message if there are extra languages
    if (Object.keys(extraLanguages).length > 0) {
      const errorDetails = Object.entries(extraLanguages)
        .map(([key, langs]) => `- Key "${key}" has translations for unsupported languages: ${langs.join(", ")}`)
        .join("\n");
      
      const errorMessage = `Found ${Object.keys(extraLanguages).length} translation keys with extra languages not in AvailableLanguages:\n${errorDetails}`;
      console.error(errorMessage);
      expect(Object.keys(extraLanguages).length).toBe(0, errorMessage);
    }
  });
});