import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useConfig = () =>
  useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
  });
