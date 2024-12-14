import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useVSCodeUrl = (config: { enabled: boolean }) => {
  const data = useQuery({
    queryKey: ["vscode_url"],
    queryFn: OpenHands.getVSCodeUrl,
    enabled: config.enabled,
    refetchOnMount: false,
  });

  return data;
};
