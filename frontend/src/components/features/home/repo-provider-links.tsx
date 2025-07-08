import { useTranslation } from "react-i18next";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import { useUserProviders } from "#/hooks/use-user-providers";

export function RepoProviderLinks() {
  const { t } = useTranslation();
  const { data: config } = useConfig();
  const { providers } = useUserProviders();

  const githubHref = config
    ? `https://github.com/apps/${config.APP_SLUG}/installations/new`
    : "";

  const hasGithubProvider = providers.includes("github");

  return (
    <div className="flex flex-col text-sm underline underline-offset-2 text-content-2 gap-4 w-fit">
      {hasGithubProvider && (
        <a href={githubHref} target="_blank" rel="noopener noreferrer">
          {t(I18nKey.HOME$ADD_GITHUB_REPOS)}
        </a>
      )}
    </div>
  );
}
