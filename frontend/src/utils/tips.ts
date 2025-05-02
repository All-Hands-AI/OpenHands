import { I18nKey } from "#/i18n/declaration";
import tipsTranslationsRaw from "#/i18n/tips.json";

export interface Tip {
  key: I18nKey;
}

// Process the tips translations to format them correctly for i18next
// This transforms the structure from:
// { "KEY": { "en": "text", "fr": "text" } }
// to:
// { "en": { "KEY": "text" }, "fr": { "KEY": "text" } }
export const tipTranslations = {};

// Get all available languages from the first tip
const availableLanguages = Object.keys(tipsTranslationsRaw[Object.keys(tipsTranslationsRaw)[0]]);

// Initialize the translation object for each language
availableLanguages.forEach(lang => {
  tipTranslations[lang] = {};
});

// Populate the translations for each language
Object.entries(tipsTranslationsRaw).forEach(([key, translations]) => {
  Object.entries(translations).forEach(([lang, text]) => {
    if (tipTranslations[lang]) {
      tipTranslations[lang][key] = text;
    }
  });
});

export const TIPS: Tip[] = [
  { key: I18nKey.TIPS$CUSTOMIZE_MICROAGENT },
  { key: I18nKey.TIPS$SETUP_SCRIPT },
  { key: I18nKey.TIPS$VSCODE_INSTANCE },
  { key: I18nKey.TIPS$SAVE_WORK },
];

export function getRandomTip(): Tip {
  const randomIndex = Math.floor(Math.random() * TIPS.length);
  return TIPS[randomIndex];
}