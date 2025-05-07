import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

interface ConfigureGitHubRepositoriesAnchorProps {
  slug: string;
}

export function ConfigureGitHubRepositoriesAnchor({
  slug,
}: ConfigureGitHubRepositoriesAnchorProps) {
  const { t } = useTranslation();

  return (
    <a
      data-testid="configure-github-repositories-button"
      href={`https://github.com/apps/${slug}/installations/new`}
      target="_blank"
      rel="noreferrer noopener"
      className="py-9"
    >
      <BrandButton type="button" variant="secondary">
        {t(I18nKey.GITHUB$CONFIGURE_REPOS)}
      </BrandButton>
    </a>
  );
}
