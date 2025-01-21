import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useGetTrajectory = () =>
  useMutation({
    mutationFn: (cid: string) => OpenHands.getTrajectory(cid),
  });
