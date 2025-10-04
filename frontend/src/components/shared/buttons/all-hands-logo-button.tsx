import { useTranslation } from "react-i18next";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { UnifiedButton } from "#/ui/unified-button/unified-button";

export function AllHandsLogoButton() {
  const { t } = useTranslation();

  return (
    <UnifiedButton
      as="NavLink"
      to="/"
      withTooltip
      tooltipContent={t(I18nKey.BRANDING$ALL_HANDS_AI)}
      ariaLabel={t(I18nKey.BRANDING$ALL_HANDS_LOGO)}
      activeClassName="text-white"
      inactiveClassName="text-[#B1B9D3]"
      tooltipProps={{
        placement: "right",
      }}
      className="bg-transparent hover:bg-transparent"
    >
      <AllHandsLogo width={46} height={30} />
    </UnifiedButton>
  );
}
