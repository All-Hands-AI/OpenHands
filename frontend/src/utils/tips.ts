import { I18nKey } from "#/i18n/declaration";

export interface Tip {
  key: I18nKey;
  link?: string;
}

export const TIPS: Tip[] = [
  { key: I18nKey.TIPS$CUSTOMIZE_MICROAGENT, link: "https://docs.all-hands.dev/docs/microagents" },
  { key: I18nKey.TIPS$SETUP_SCRIPT, link: "https://docs.all-hands.dev/docs/setup-script" },
  { key: I18nKey.TIPS$VSCODE_INSTANCE },
  { key: I18nKey.TIPS$SAVE_WORK },
];

export function getRandomTip(): Tip {
  const randomIndex = Math.floor(Math.random() * TIPS.length);
  return TIPS[randomIndex];
}
