import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useLogout = () =>
  useMutation({
    mutationFn: OpenHands.logout,
  });
