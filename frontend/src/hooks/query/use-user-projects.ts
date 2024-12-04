import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "./use-is-authed";

export const useUserProjects = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["projects"],
    queryFn: OpenHands.getUserProjects,
    enabled: !!userIsAuthenticated,
  });
};
