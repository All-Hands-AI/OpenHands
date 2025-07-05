import { useQuery } from "@tanstack/react-query";
import { userService } from "#/api/user-service/user-service.api";
import { useConfig } from "./use-config";

export const useMe = () => {
  const { data: config } = useConfig();
  const isSaas = config?.APP_MODE === "saas";

  return useQuery({
    queryKey: ["user", "me"],
    queryFn: userService.getMe,
    enabled: isSaas,
  });
};
