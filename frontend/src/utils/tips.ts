import { I18nKey } from "#/i18n/declaration";

export interface Tip {
  key: I18nKey;
}

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
