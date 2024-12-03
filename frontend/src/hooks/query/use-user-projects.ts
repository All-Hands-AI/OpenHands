import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useUserProjects = () =>
  useQuery({
    queryKey: ["projects"],
    queryFn: OpenHands.getUserProjects,
  });
