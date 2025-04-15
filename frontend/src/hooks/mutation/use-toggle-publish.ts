import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useConversation } from "#/context/conversation-context"
import { displayErrorToast } from "#/utils/custom-toast-handlers"
import OpenHands from "#/api/open-hands"

interface TogglePublishArgs {
  isPublished: boolean
}

export const useConversationVisibility = () => {
  const { conversationId } = useConversation()

  return useQuery({
    queryKey: [`conversation-visibility-${conversationId}`],
    queryFn: async () => {
      if (!conversationId) {
        return false
      }
      return await OpenHands.getConversationVisibility(conversationId)
    },
    enabled: !!conversationId,
  })
}

export const useTogglePublish = () => {
  const { conversationId } = useConversation()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ isPublished }: TogglePublishArgs) => {
      if (!conversationId) {
        throw new Error("No conversation ID available")
      }

      const success = await OpenHands.changeConversationVisibility(
        conversationId,
        isPublished,
      )

      if (!success) {
        throw new Error("Failed to update publish status")
      }

      return { success, isPublished }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [`conversation-${conversationId}`],
      })
      queryClient.invalidateQueries({
        queryKey: [`conversation-visibility-${conversationId}`],
      })
    },
    onError: (error) => {
      displayErrorToast(error.message || "Failed to update publish status")
    },
  })
}
