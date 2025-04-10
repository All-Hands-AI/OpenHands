import { useTranslation } from "react-i18next"
import CheckmarkIcon from "#/icons/checkmark.svg?react"
import CopyIcon from "#/icons/copy.svg?react"
import { I18nKey } from "#/i18n/declaration"

interface CopyToClipboardButtonProps {
  isHidden: boolean
  isDisabled: boolean
  onClick: () => void
  mode: "copy" | "copied"
}

export function CopyToClipboardButton({
  isHidden,
  isDisabled,
  onClick,
  mode,
}: CopyToClipboardButtonProps) {
  const { t } = useTranslation()
  return (
    <button
      hidden={isHidden}
      disabled={isDisabled}
      data-testid="copy-to-clipboard"
      type="button"
      onClick={onClick}
      className="absolute right-1 top-1 rounded bg-neutral-1000 p-1 text-neutral-100 dark:bg-neutral-300 dark:text-white"
      aria-label={t(
        mode === "copy" ? I18nKey.BUTTON$COPY : I18nKey.BUTTON$COPIED,
      )}
    >
      {mode === "copy" && <CopyIcon width={15} height={15} />}
      {mode === "copied" && <CheckmarkIcon width={15} height={15} />}
    </button>
  )
}
