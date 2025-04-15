import { useIsMutating } from "@tanstack/react-query";

export const useIsCreatingConversation = () => {
  const numberOfPendingMutations = useIsMutating({
    mutationKey: ["create-conversation"],
  });

  return numberOfPendingMutations > 0;
};
