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
    <div data-testid="configure-github-repositories-button" className="py-9">
      <BrandButton
        type="button"
        variant="primary"
        className="w-55"
        onClick={() =>
          window.open(
            `https://github.com/apps/${slug}/installations/new`,
            "_blank",
            "noreferrer noopener",
          )
        }
      >
        {t(I18nKey.GITHUB$CONFIGURE_REPOS)}
      </BrandButton>
    </div>
  );
}
