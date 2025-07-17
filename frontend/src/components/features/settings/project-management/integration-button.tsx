import React from "react";
import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";

interface IntegrationButtonProps {
  isLoading: boolean;
  isLinked: boolean;
  onClick: () => void;
  "data-testid"?: string;
}

export function IntegrationButton({
  isLoading,
  isLinked,
  onClick,
  "data-testid": dataTestId,
}: IntegrationButtonProps) {
  const { t } = useTranslation();

  return (
    <BrandButton
      data-testid={dataTestId}
      variant={isLinked ? "secondary" : "primary"}
      onClick={onClick}
      isDisabled={isLoading}
      type="button"
      className="w-20 min-w-20"
    >
      {isLoading && t(I18nKey.SETTINGS$SAVING)}
      {!isLoading &&
        (isLinked
          ? t(I18nKey.PROJECT_MANAGEMENT$UNLINK_BUTTON_LABEL)
          : t(I18nKey.PROJECT_MANAGEMENT$LINK_BUTTON_LABEL))}
    </BrandButton>
  );
}
