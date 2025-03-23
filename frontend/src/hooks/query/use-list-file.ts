import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { QueryKeys } from "#/utils/query/query-keys";
import { useFileStateContext } from "#/context/file-state-context";

interface UseListFileConfig {
  path: string;
  enabled?: boolean;
}

/**
 * Hook to get a file's content
 * Uses React Query for data fetching and caching
 * Integrates with the file state context to handle unsaved changes
 */
export const useListFile = (config: UseListFileConfig) => {
  const { conversationId } = useConversation();
  const { getFileState, addOrUpdateFileState } = useFileStateContext();

  // Get file content from API
  const query = useQuery({
    queryKey: QueryKeys.file(conversationId, config.path),
    queryFn: () => OpenHands.getFile(conversationId, config.path),
    enabled: config.enabled ?? false, // don't fetch by default, trigger manually via `refetch`
  });

  // When file content is loaded, update the file state
  const { data: content } = query;

  // Save file content to state when it's loaded
  const fileState = getFileState(config.path);
  if (content && !fileState) {
    addOrUpdateFileState({
      path: config.path,
      savedContent: content,
      unsavedContent: content,
    });
  }

  // Get content from file state if available, otherwise from API
  const currentContent = fileState?.unsavedContent ?? content;

  // Save file content
  const saveFile = useCallback(
    async (newContent: string) => {
      try {
        await OpenHands.saveFile(conversationId, config.path, newContent);

        // Update file state with new saved content
        addOrUpdateFileState({
          path: config.path,
          savedContent: newContent,
          unsavedContent: newContent,
        });

        return true;
      } catch (error) {
        // Error is handled by React Query's global error handler
        return false;
      }
    },
    [conversationId, config.path, addOrUpdateFileState],
  );

  // Update unsaved content without saving to server
  const updateUnsavedContent = useCallback(
    (newContent: string) => {
      const currentState = getFileState(config.path);
      if (currentState) {
        addOrUpdateFileState({
          path: config.path,
          savedContent: currentState.savedContent,
          unsavedContent: newContent,
        });
      } else if (content) {
        addOrUpdateFileState({
          path: config.path,
          savedContent: content,
          unsavedContent: newContent,
        });
      }
    },
    [config.path, content, getFileState, addOrUpdateFileState],
  );

  return {
    ...query,
    currentContent,
    saveFile,
    updateUnsavedContent,
    isChanged: fileState?.changed || false,
  };
};
