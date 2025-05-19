import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useConfig } from "../query/use-config";

export const useLogout = () => {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: () => OpenHands.logout(config?.APP_MODE ?? "oss"),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: ["tasks"] });
      queryClient.removeQueries({ queryKey: ["settings"] });
      queryClient.removeQueries({ queryKey: ["user"] });
      queryClient.removeQueries({ queryKey: ["secrets"] });

      posthog.reset();
      await navigate("/");
    },
  });
};
