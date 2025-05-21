import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

interface ConfigureAzureDevOpsRepositoriesAnchorProps {
  organizationUrl: string;
}

export function ConfigureAzureDevOpsRepositoriesAnchor({
  organizationUrl,
}: ConfigureAzureDevOpsRepositoriesAnchorProps) {
  const { t } = useTranslation();

  // Ensure the URL has the correct format
  const formattedUrl = organizationUrl.endsWith("/")
    ? organizationUrl
    : `${organizationUrl}/`;

  return (
    <a
      data-testid="configure-azure-devops-repositories-button"
      href={`${formattedUrl}_git`}
      target="_blank"
      rel="noreferrer noopener"
      className="py-9"
    >
      <BrandButton type="button" variant="secondary">
        {t(I18nKey.AZURE_DEVOPS$CONFIGURE_REPOS)}
      </BrandButton>
    </a>
  );
}
