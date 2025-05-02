import { I18nKey } from "#/i18n/declaration";
import tipsTranslations from "#/i18n/tips.json";

export interface Tip {
  key: I18nKey;
}

// Add the tips translations to the i18n resources
export const tipTranslations = tipsTranslations;

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