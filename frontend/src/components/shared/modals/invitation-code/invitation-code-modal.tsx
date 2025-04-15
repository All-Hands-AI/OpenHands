import React, { useState } from "react"
import { BaseModal } from "../base-modal/base-modal"
import { openHands } from "#/api/open-hands-axios"
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers"

interface InvitationCodeModalProps {
  isOpen: boolean
  onOpenChange: (isOpen: boolean) => void
  onSuccess?: () => void
}

export function InvitationCodeModal({
  isOpen,
  onOpenChange,
  onSuccess,
}: InvitationCodeModalProps) {
  const [invitationCode, setInvitationCode] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Reset input field when modal is opened or closed
  React.useEffect(() => {
    if (!isOpen) {
      // Reset the field after modal is closed
      setTimeout(() => setInvitationCode(""), 300)
    }
  }, [isOpen])

  const handleSubmit = async () => {
    if (!invitationCode.trim()) {
      displayErrorToast("Please enter an invitation code")
      return
    }

    setIsSubmitting(true)
    try {
      const response = await openHands.post(
        `/api/invitation/validate/${invitationCode.trim()}`,
      )

      if (response.data.valid) {
        displaySuccessToast(
          response.data.message || "Successfully activated account",
        )
        onSuccess?.()
        onOpenChange(false)
      } else {
        displayErrorToast(response.data.reason || "Invalid invitation code")
        setInvitationCode("")
      }
    } catch (error: any) {
      displayErrorToast(
        error.response?.data?.detail || "Failed to validate invitation code",
      )
      setInvitationCode("")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title="Enter Invitation Code"
      isDismissable={false}
      actions={[
        {
          label: isSubmitting ? "Submitting..." : "Submit",
          action: handleSubmit,
          isDisabled: isSubmitting || !invitationCode.trim(),
          className: "bg-blue-600 text-white hover:bg-blue-700",
          closeAfterAction: false,
        },
      ]}
      testID="invitation-code-modal"
    >
      <div className="w-full">
        <input
          type="text"
          value={invitationCode}
          onChange={(e) => setInvitationCode(e.target.value)}
          placeholder="Enter your invitation code"
          className="w-full rounded-md border border-gray-300 bg-white p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800"
          disabled={isSubmitting}
          data-testid="invitation-code-input"
        />
      </div>
    </BaseModal>
  )
}
