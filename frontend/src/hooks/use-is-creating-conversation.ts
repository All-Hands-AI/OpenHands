import { useIsMutating } from "@tanstack/react-query";
import { useNavigation } from "react-router";

export const useIsCreatingConversation = () => {
  const navigation = useNavigation();
  const numberOfPendingMutations = useIsMutating({
    mutationKey: ["create-conversation"],
  });

  const isNavigating = Boolean(navigation.location);
  const hasPendingMutations = numberOfPendingMutations > 0;

  return hasPendingMutations || isNavigating;
};
