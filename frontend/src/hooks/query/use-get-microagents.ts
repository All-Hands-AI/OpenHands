import { useQuery } from "@tanstack/react-query";
import { useConversationId } from "../use-conversation-id";
import { FileService } from "#/api/file-service/file-service.api";

export const useGetMicroagents = (microagentDirectory: string) => {
  const { conversationId } = useConversationId();

  return useQuery({
    queryKey: ["files", "microagents", conversationId, microagentDirectory],
    queryFn: () => FileService.getFiles(conversationId!, microagentDirectory),
    enabled: !!conversationId,
    select: (data) =>
      data.map((fileName) => fileName.replace(microagentDirectory, "")),
  });
};
