import { I18nKey } from "#/i18n/declaration";

export interface Tip {
  key: I18nKey;
  link?: string;
}

export const TIPS: Tip[] = [
  {
    key: I18nKey.TIPS$CUSTOMIZE_MICROAGENT,
    link: "https://docs.all-hands.dev/modules/usage/prompting/microagents-repo",
  },
  {
    key: I18nKey.TIPS$SETUP_SCRIPT,
    link: "https://docs.all-hands.dev/modules/usage/customization/repository",
  },
  { key: I18nKey.TIPS$VSCODE_INSTANCE },
  { key: I18nKey.TIPS$SAVE_WORK },
  {
    key: I18nKey.TIPS$SPECIFY_FILES,
    link: "https://docs.all-hands.dev/modules/usage/prompting/prompting-best-practices",
  },
  {
    key: I18nKey.TIPS$HEADLESS_MODE,
    link: "https://docs.all-hands.dev/modules/usage/how-to/headless-mode",
  },
  {
    key: I18nKey.TIPS$CLI_MODE,
    link: "https://docs.all-hands.dev/modules/usage/how-to/cli-mode",
  },
  {
    key: I18nKey.TIPS$GITHUB_HOOK,
    link: "https://docs.all-hands.dev/modules/usage/cloud/cloud-issue-resolver",
  },
  {
    key: I18nKey.TIPS$BLOG_SIGNUP,
    link: "https://www.all-hands.dev/blog",
  },
  {
    key: I18nKey.TIPS$API_USAGE,
    link: "https://docs.all-hands.dev/swagger-ui/",
  },
];

export function getRandomTip(): Tip {
  const randomIndex = Math.floor(Math.random() * TIPS.length);
  return TIPS[randomIndex];
}
