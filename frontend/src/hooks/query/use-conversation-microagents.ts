import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Microagent } from "#/api/open-hands.types";

interface UseConversationMicroagentsOptions {
  conversationId: string | undefined;
  enabled?: boolean;
}

interface UseConversationMicroagentsResult {
  microagents: Microagent[] | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useConversationMicroagents = ({
  conversationId,
  enabled = true,
}: UseConversationMicroagentsOptions): UseConversationMicroagentsResult => {
  const query = useQuery({
    queryKey: ["conversation", conversationId, "microagents"],
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("No conversation ID provided");
      }
      const data = await OpenHands.getMicroagents(conversationId);
      return data.microagents;
    },
    enabled: !!conversationId && enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  return {
    microagents: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
};
