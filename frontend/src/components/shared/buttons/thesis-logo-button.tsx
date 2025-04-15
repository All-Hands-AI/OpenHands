import { useTranslation } from "react-i18next"
import thesisLogo from "#/assets/branding/thesis-logo.png"
import { TooltipButton } from "./tooltip-button"

interface ThesisLogoButtonProps {
  onClick: () => void
}

export function ThesisLogoButton({ onClick }: ThesisLogoButtonProps) {
  const { t } = useTranslation()
  return (
    <TooltipButton tooltip="Thesis" ariaLabel="Thesis Logo" onClick={onClick}>
      <img
        src={thesisLogo}
        alt="Thesis Logo"
        width={32}
        height={32}
        className="rounded"
      />
    </TooltipButton>
  )
}
