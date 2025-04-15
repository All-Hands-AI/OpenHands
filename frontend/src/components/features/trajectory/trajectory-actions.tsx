import { useTranslation } from "react-i18next"
import { I18nKey } from "#/i18n/declaration"
import ThumbsUpIcon from "#/icons/thumbs-up.svg?react"
import ThumbDownIcon from "#/icons/thumbs-down.svg?react"
import ExportIcon from "#/icons/export.svg?react"
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button"
import { FaShare } from "react-icons/fa"
import { useState } from "react"
import { ShareModal } from "./share-modal"

interface TrajectoryActionsProps {
  onPositiveFeedback: () => void
  onNegativeFeedback: () => void
  onExportTrajectory: () => void
}

export function TrajectoryActions({
  onPositiveFeedback,
  onNegativeFeedback,
  onExportTrajectory,
}: TrajectoryActionsProps) {
  const { t } = useTranslation()
  const [shareModalOpen, setShareModalOpen] = useState(false)

  const handleShare = () => {
    setShareModalOpen(true)
  }

  return (
    <>
      <div data-testid="feedback-actions" className="flex gap-1">
        <TrajectoryActionButton
          testId="positive-feedback"
          onClick={onPositiveFeedback}
          icon={<ThumbsUpIcon width={15} height={15} />}
          tooltip={t(I18nKey.BUTTON$MARK_HELPFUL)}
        />
        <TrajectoryActionButton
          testId="negative-feedback"
          onClick={onNegativeFeedback}
          icon={<ThumbDownIcon width={15} height={15} />}
          tooltip={t(I18nKey.BUTTON$MARK_NOT_HELPFUL)}
        />
        <TrajectoryActionButton
          testId="export-trajectory"
          onClick={onExportTrajectory}
          icon={<ExportIcon width={15} height={15} />}
          tooltip={t(I18nKey.BUTTON$EXPORT_CONVERSATION)}
        />
        <TrajectoryActionButton
          testId="share-conversation"
          onClick={handleShare}
          icon={<FaShare size={15} />}
          tooltip={"Share Conversation"}
        />
      </div>

      <ShareModal isOpen={shareModalOpen} onOpenChange={setShareModalOpen} />
    </>
  )
}
