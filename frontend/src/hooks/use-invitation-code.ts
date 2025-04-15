import { useState, useEffect, useCallback } from "react"
import { openHands } from "#/api/open-hands-axios"
import usePersistStore from "#/zutand-stores/persist-config/usePersistStore"

/**
 * A hook to check if the user needs to enter an invitation code
 * and manage the invitation modal state
 */
export function useInvitationCode() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [needsInvitation, setNeedsInvitation] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const { jwt } = usePersistStore()

  const checkUserStatus = useCallback(async () => {
    console.trace("checkUserSttatus")
    if (!jwt) {
      setIsLoading(false)
      setNeedsInvitation(false)
      return
    }

    try {
      setIsLoading(true)
      const response = await openHands.get("/api/user/status")

      // If user status is not "activated", they need an invitation code
      if (response.data.status !== "activated") {
        setNeedsInvitation(true)
      } else {
        setNeedsInvitation(false)
      }
    } catch (error) {
      console.error("Error checking user status:", error)
      // If there's an error, assume they might need an invitation
      setNeedsInvitation(true)
    } finally {
      setIsLoading(false)
    }
  }, [jwt])

  // Function to refresh status after successful activation
  const refreshStatus = useCallback(async () => {
    await checkUserStatus()
  }, [checkUserStatus])

  useEffect(() => {
    console.log("checkUserStatus")

    checkUserStatus()
  }, [checkUserStatus])

  return {
    isModalOpen,
    setIsModalOpen,
    needsInvitation,
    isLoading,
    refreshStatus,
  }
}
