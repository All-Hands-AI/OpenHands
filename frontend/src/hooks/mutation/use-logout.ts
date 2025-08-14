import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useConfig } from "../query/use-config";
import { clearLoginData } from "#/utils/local-storage";

export const useLogout = () => {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();

  const performClientSideLogout = () => {
    queryClient.removeQueries({ queryKey: ["tasks"] });
    queryClient.removeQueries({ queryKey: ["settings"] });
    queryClient.removeQueries({ queryKey: ["user"] });
    queryClient.removeQueries({ queryKey: ["secrets"] });

    // Clear login method and last page from local storage
    if (config?.APP_MODE === "saas") {
      clearLoginData();
    }

    posthog.reset();

    // Refresh the page after all logout logic is completed
    window.location.reload();
  };

  return useMutation({
    mutationFn: () => OpenHands.logout(config?.APP_MODE ?? "oss"),
    onSuccess: performClientSideLogout,
    onError: (error) => {
      // If logout API call fails (e.g., due to 401), still perform client-side cleanup
      // This is especially important when users are stuck in a 401 state
      console.warn("Logout API call failed, performing client-side cleanup:", error);
      performClientSideLogout();
    },
  });
};
