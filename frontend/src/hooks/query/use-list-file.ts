import { useConversation } from "#/context/conversation-context"
import { useQuery } from "@tanstack/react-query"
import { FileService } from "#/api/file-service/file-service.api"

interface UseListFileConfig {
  path: string
  enabled?: boolean
}

export const useListFile = (config: UseListFileConfig) => {
  const { conversationId } = useConversation()
  return useQuery({
    queryKey: ["files", conversationId, config.path],
    queryFn: () => FileService.getFile(conversationId, config.path),
    enabled: config?.enabled, // don't fetch by default, trigger manually via `refetch`
  })
}
