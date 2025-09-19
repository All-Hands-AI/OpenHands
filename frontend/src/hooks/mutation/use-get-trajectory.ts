import { useMutation } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";

export const useGetTrajectory = () =>
  useMutation({
    mutationFn: (cid: string) => ConversationService.getTrajectory(cid),
  });
