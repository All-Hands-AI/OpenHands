import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useSettings } from "#/hooks/query/use-settings";

export function ConnectToProviderMessage() {
  const { isLoading } = useSettings();
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4">
      <p>{t("HOME$CONNECT_PROVIDER_MESSAGE")}</p>
      <Link
        data-testid="navigate-to-settings-button"
        to="/settings/integrations"
      >
        <BrandButton type="button" variant="primary" isDisabled={isLoading}>
          {!isLoading && t("SETTINGS$TITLE")}
          {isLoading && t("HOME$LOADING")}
        </BrandButton>
      </Link>
    </div>
  );
}
