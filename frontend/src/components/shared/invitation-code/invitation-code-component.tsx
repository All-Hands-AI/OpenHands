import React, { useState } from "react"
import { openHands } from "#/api/open-hands-axios"
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers"
import InviteCodeIcon from "#/assets/invite-code.svg?react"
interface InvitationCodeComponentProps {
  onSuccess?: () => void
}

export function InvitationCodeComponent({
  onSuccess,
}: InvitationCodeComponentProps) {
  const [invitationCode, setInvitationCode] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

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
        setInvitationCode("")
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
    <div className="mx-auto w-full max-w-md rounded-lg p-8">
      <div className="flex flex-col items-center">
        <div className="p-4">
          <InviteCodeIcon />
        </div>

        <h1 className="mb-2 text-center text-4xl font-bold">
          Welcome to Thesis!
        </h1>
        <p className="mb-6 text-center text-gray-600">
          Thesis is in early access. Please enter your invite code to continue
        </p>

        <div className="w-full">
          <label
            htmlFor="invitation-code"
            className="mb-1 block text-sm font-medium text-[#1F1F1F]"
          >
            Invitation code*
          </label>
          <input
            id="invitation-code"
            type="text"
            value={invitationCode}
            onChange={(e) => setInvitationCode(e.target.value)}
            placeholder="Enter your invitation code"
            className="w-full rounded-md bg-white p-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={isSubmitting}
            data-testid="invitation-code-input"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={isSubmitting || !invitationCode.trim()}
          className="mt-4 w-full rounded-md bg-blue-500 py-3 font-medium text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
          data-testid="invitation-code-submit"
        >
          {isSubmitting ? "Submitting..." : "Continue"}
        </button>
      </div>
    </div>
  )
}
