import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useGetTrajectorySummary = () =>
  useMutation({
    mutationFn: (cid: string) => OpenHands.getTrajectorySummary(cid),
  });
