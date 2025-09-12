import React from "react";
import { useTranslation } from "react-i18next";
import { UpgradeBanner } from "#/components/features/settings";

interface UpgradeBannerWithBackdropProps {
  onUpgradeClick: () => void;
  isDisabled?: boolean;
}

export function UpgradeBannerWithBackdrop({
  onUpgradeClick,
  isDisabled,
}: UpgradeBannerWithBackdropProps) {
  const { t } = useTranslation();

  return (
    <>
      <UpgradeBanner
        message={t("SETTINGS$UPGRADE_BANNER_MESSAGE")}
        onUpgradeClick={onUpgradeClick}
        className="sticky top-0 z-10"
        isDisabled={isDisabled}
      />
      <div
        data-testid="settings-backdrop"
        className="absolute top-12 left-0 right-0 bottom-0 z-20"
        style={{
          opacity: 0.5,
          background: "#26282D",
        }}
      />
    </>
  );
}
