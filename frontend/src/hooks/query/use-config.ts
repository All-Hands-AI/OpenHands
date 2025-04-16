import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useDisableApiOnTos } from "../use-disable-api-on-tos";

export const useConfig = () => {
  const disableApiCalls = useDisableApiOnTos();

  return useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes,
    enabled: !disableApiCalls,
  });
};
