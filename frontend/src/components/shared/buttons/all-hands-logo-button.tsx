import { useTranslation } from "react-i18next"
// import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import Logo from "#/assets/branding/logo.jpg"
import { TooltipButton } from "./tooltip-button"

interface AllHandsLogoButtonProps {
  onClick: () => void
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  const { t } = useTranslation()
  return (
    <TooltipButton tooltip="Thesis" ariaLabel="Thesis Logo" onClick={onClick}>
      {/* <AllHandsLogo /> */}
      <img
        src={Logo}
        alt="Thesis Logo"
        width={32}
        height={32}
        className="rounded"
      />
    </TooltipButton>
  )
}
