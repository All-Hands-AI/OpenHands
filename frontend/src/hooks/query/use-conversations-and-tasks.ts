import { useQueries } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import V1ConversationService, {
  V1AppConversationStartTask,
} from "#/api/conversation-service/v1-conversation-service.api";
import { Conversation, ConversationTrigger } from "#/api/open-hands.types";

/**
 * Unified type that represents either a conversation or a task
 * This allows the UI to render a single list of both
 */
export type ConversationOrTask =
  | {
      type: "conversation";
      data: Conversation;
      id: string;
      title: string;
      created_at: string;
      updated_at: string;
      selected_repository: string | null;
      status: string;
    }
  | {
      type: "task";
      data: V1AppConversationStartTask;
      id: string;
      title: string | null;
      created_at: string;
      updated_at: string;
      selected_repository: string | null;
      status: string;
    };

/**
 * Hook that fetches both V0 conversations and V1 start tasks and combines them into a single list
 * This is useful for showing all ongoing work to the user, including:
 * - Completed conversations (V0 and V1)
 * - In-progress start tasks (V1) that haven't completed yet
 *
 * Use case: When a user starts a conversation and navigates back, they should see the in-progress task
 */
export const useConversationsAndTasks = (
  selectedRepository?: string,
  conversationTrigger?: ConversationTrigger,
  limit: number = 100,
  cacheDisabled: boolean = false,
) => {
  const results = useQueries({
    queries: [
      // Query 1: Fetch V0 conversations
      {
        queryKey: [
          "conversations",
          "search",
          selectedRepository,
          conversationTrigger,
          limit,
        ],
        queryFn: () =>
          ConversationService.searchConversations(
            selectedRepository,
            conversationTrigger,
            limit,
          ),
        staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
        gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
      },
      // Query 2: Fetch V1 start tasks
      {
        queryKey: [
          "start-tasks",
          "search",
          selectedRepository,
          conversationTrigger,
          limit,
        ],
        queryFn: () =>
          V1ConversationService.searchStartTasks(
            selectedRepository,
            conversationTrigger,
            limit,
          ),
        staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
        gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
      },
    ],
  });

  const [conversationsQuery, tasksQuery] = results;

  // Transform conversations to unified format
  const conversations: ConversationOrTask[] =
    conversationsQuery.data?.map((conv) => ({
      type: "conversation" as const,
      data: conv,
      id: conv.conversation_id,
      title: conv.title,
      created_at: conv.created_at,
      updated_at: conv.last_updated_at,
      selected_repository: conv.selected_repository,
      status: conv.status,
    })) || [];

  // Transform tasks to unified format
  const tasks: ConversationOrTask[] =
    tasksQuery.data?.map((task) => ({
      type: "task" as const,
      data: task,
      id: task.id,
      title: task.request.title || null,
      created_at: task.created_at,
      updated_at: task.updated_at,
      selected_repository: task.request.selected_repository ?? null,
      status: task.status,
    })) || [];

  // Combine and sort by updated_at (most recent first)
  const combined = [...conversations, ...tasks].sort((a, b) => {
    const aTime = new Date(a.updated_at).getTime();
    const bTime = new Date(b.updated_at).getTime();
    return bTime - aTime; // Descending order (newest first)
  });

  return {
    data: combined,
    conversations,
    tasks,
    isLoading: conversationsQuery.isLoading || tasksQuery.isLoading,
    isError: conversationsQuery.isError || tasksQuery.isError,
    error: conversationsQuery.error || tasksQuery.error,
    refetch: () => {
      conversationsQuery.refetch();
      tasksQuery.refetch();
    },
  };
};
