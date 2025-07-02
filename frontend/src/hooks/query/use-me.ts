import { useQuery } from "@tanstack/react-query";
import { userService } from "#/api/user-service/user-service.api";

export const useMe = () =>
  useQuery({
    queryKey: ["user", "me"],
    queryFn: userService.getUser,
  });
