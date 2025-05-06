import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import OpenHands from "#/api/open-hands";
import { useConfig } from "../query/use-config";

export const useLogout = () => {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: () => OpenHands.logout(config?.APP_MODE ?? "oss"),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.removeQueries({ queryKey: ["tasks"] });
      queryClient.removeQueries({ queryKey: ["settings"] });
      queryClient.removeQueries({ queryKey: ["user"] });

      await navigate("/");
    },
  });
};
