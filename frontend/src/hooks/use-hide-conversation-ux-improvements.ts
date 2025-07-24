import { useConfig } from "#/hooks/query/use-config";

/**
 * Custom hook that determines whether the conversation UX improvements feature should be hidden.
 *
 * @returns true if HIDE_CONVERSATION_UX_IMPROVEMENTS is enabled in the config; otherwise, returns false
 */
export const useHideConversationUxImprovements = (): boolean => {
  const { data: config } = useConfig();

  // Return true if the feature flag is enabled, false otherwise
  // Default to false if config is not available or the flag is not set
  return config?.FEATURE_FLAGS.HIDE_CONVERSATION_UX_IMPROVEMENTS ?? false;
};
