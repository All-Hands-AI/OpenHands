import { useState, useEffect } from "react"
import { BaseModal } from "#/components/shared/modals/base-modal/base-modal"
import { Switch } from "@heroui/react"
import { useConversation } from "#/context/conversation-context"
import {
  displaySuccessToast,
  displayErrorToast,
} from "#/utils/custom-toast-handlers"
import CopyIcon from "#/icons/copy.svg?react"
import {
  useTogglePublish,
  useConversationVisibility,
} from "#/hooks/mutation/use-toggle-publish"

interface ShareModalProps {
  isOpen: boolean
  onOpenChange: (isOpen: boolean) => void
  initialPublishState?: boolean
}

export function ShareModal({
  isOpen,
  onOpenChange,
  initialPublishState = false,
}: ShareModalProps) {
  const { conversationId } = useConversation()
  const [isPublished, setIsPublished] = useState(initialPublishState)
  const { mutate: togglePublish, isPending: isToggling } = useTogglePublish()
  const { data: visibility, isLoading: isLoadingVisibility } =
    useConversationVisibility()

  useEffect(() => {
    if (visibility !== undefined) {
      setIsPublished(visibility)
    }
  }, [visibility])

  const shareUrl = conversationId
    ? `${window.location.origin}/share/${conversationId}`
    : ""

  const handlePublishToggle = async () => {
    if (!conversationId) return

    togglePublish(
      { isPublished: !isPublished },
      {
        onSuccess: (data) => {
          setIsPublished(!isPublished)
          displaySuccessToast(
            !isPublished
              ? "Conversation is now public"
              : "Conversation is now private",
          )
        },
      },
    )
  }

  const copyShareLink = () => {
    if (!shareUrl) return

    navigator.clipboard
      .writeText(shareUrl)
      .then(() => {
        displaySuccessToast("Share URL copied to clipboard!")
      })
      .catch((err) => {
        console.error("Could not copy URL: ", err)
        displayErrorToast("Failed to copy URL")
      })
  }

  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title="Share Conversation"
      testID="share-modal"
      contentClassName="max-w-[30rem] p-[40px] bg-white dark:bg-base-secondary rounded-lg"
    >
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-base font-medium text-neutral-100 dark:text-white">
              Make conversation public
            </span>
            <span className="text-sm text-neutral-700 dark:text-neutral-400">
              Allow others to view this conversation with a link
            </span>
          </div>
          <Switch
            isSelected={isPublished}
            onValueChange={handlePublishToggle}
            isDisabled={isToggling || isLoadingVisibility}
            aria-label="Publish conversation"
          />
        </div>

        {isPublished && (
          <div className="flex flex-col gap-2">
            <span className="text-sm text-neutral-700 dark:text-neutral-400">
              Share link
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="w-full rounded bg-neutral-1000 px-3 py-[10px] text-sm text-neutral-100 dark:bg-[#27272A] dark:text-white"
              />
              <button
                onClick={copyShareLink}
                className="rounded bg-neutral-1000 p-2 text-neutral-100 transition-colors hover:bg-neutral-900 dark:bg-[#27272A] dark:text-white dark:hover:bg-[#323238]"
                aria-label="Copy share link"
              >
                <CopyIcon width={20} height={20} />
              </button>
            </div>
          </div>
        )}
      </div>
    </BaseModal>
  )
}
