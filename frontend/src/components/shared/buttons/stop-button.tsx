import PauseIcon from "#/icons/pause.svg?react"
import { useTranslation } from "react-i18next"
import { I18nKey } from "#/i18n/declaration"

interface StopButtonProps {
  isDisabled?: boolean
  onClick?: () => void
}

export function StopButton({ isDisabled, onClick }: StopButtonProps) {
  const { t } = useTranslation()
  return (
    <button
      data-testid="stop-button"
      aria-label={t(I18nKey.BUTTON$STOP)}
      disabled={isDisabled}
      onClick={onClick}
      type="button"
      className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary hover:bg-primary/90 focus:bg-primary/90"
    >
      <PauseIcon className="h-5 w-5 text-white" />
    </button>
  )
}
