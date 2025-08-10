import { useQuery } from "@tanstack/react-query";
import { useConversationId } from "../use-conversation-id";
import OpenHands from "#/api/open-hands";

export const useGetMicroagents = (microagentDirectory: string) => {
  const { conversationId } = useConversationId();

  return useQuery({
    queryKey: ["files", "microagents", conversationId, microagentDirectory],
    queryFn: () => OpenHands.getFiles(conversationId!, microagentDirectory),
    enabled: !!conversationId,
    select: (data) =>
      data.map((fileName) => fileName.replace(microagentDirectory, "")),
  });
};
