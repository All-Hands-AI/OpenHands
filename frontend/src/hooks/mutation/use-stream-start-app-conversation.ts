import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import AppConversationService from "#/api/app-conversation-service/app-conversation-service.api";
import {
  AppConversationStartRequest,
  AppConversationStartTask,
} from "#/api/open-hands.types";

interface StreamStartAppConversationVariables {
  request: AppConversationStartRequest;
  onProgress?: (task: AppConversationStartTask) => void;
}

interface StreamStartAppConversationResult {
  finalTask: AppConversationStartTask | null;
  allTasks: AppConversationStartTask[];
}

export const useStreamStartAppConversation = () => {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const mutation = useMutation({
    mutationKey: ["stream-start-app-conversation"],
    mutationFn: async (
      variables: StreamStartAppConversationVariables,
    ): Promise<StreamStartAppConversationResult> => {
      const { request, onProgress } = variables;

      // Create a new AbortController for this request
      abortControllerRef.current = new AbortController();

      const allTasks: AppConversationStartTask[] = [];
      let finalTask: AppConversationStartTask | null = null;

      try {
        // eslint-disable-next-line no-await-in-loop -- Sequential processing required for streaming
        for await (const task of AppConversationService.streamStartAppConversation(
          request,
        )) {
          // Check if the request was aborted
          if (abortControllerRef.current?.signal.aborted) {
            throw new Error("Request was cancelled");
          }

          allTasks.push(task);
          finalTask = task;

          // Call the progress callback if provided
          if (onProgress) {
            onProgress(task);
          }

          // If we reach READY or ERROR status, we're done
          if (task.status === "READY" || task.status === "ERROR") {
            break;
          }
        }
      } catch (error) {
        // If it's not a cancellation error, re-throw it
        if (
          error instanceof Error &&
          error.message !== "Request was cancelled"
        ) {
          throw error;
        }
        // For cancellation, we still return what we have so far
      } finally {
        abortControllerRef.current = null;
      }

      return { finalTask, allTasks };
    },
    onSuccess: async (result) => {
      // Invalidate relevant queries when the conversation is successfully started
      if (result.finalTask?.status === "READY") {
        await queryClient.invalidateQueries({
          queryKey: ["app-conversations"],
        });

        // You might also want to invalidate other related queries
        await queryClient.invalidateQueries({
          queryKey: ["user", "conversations"],
        });
      }
    },
    onError: (error) => {
      console.error("Error starting app conversation:", error);
    },
  });

  return {
    ...mutation,
    cancelStream,
    isStreaming: mutation.isPending,
  };
};

// Additional hook for simpler usage when you just want the final result
export const useStartAppConversation = () => {
  const streamMutation = useStreamStartAppConversation();

  const startConversation = useCallback(
    (request: AppConversationStartRequest) =>
      streamMutation.mutateAsync({ request }),
    [streamMutation],
  );

  return {
    startConversation,
    isLoading: streamMutation.isPending,
    error: streamMutation.error,
    data: streamMutation.data,
    reset: streamMutation.reset,
  };
};
