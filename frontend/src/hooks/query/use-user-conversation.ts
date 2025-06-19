/* eslint-disable @typescript-eslint/no-explicit-any */
import { Query, useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";

const FIVE_MINUTES = 1000 * 60 * 5;
const FIFTEEN_MINUTES = 1000 * 60 * 15;
type RefetchInterval = (
  query: Query<
    Conversation | null,
    AxiosError<unknown, any>,
    Conversation | null,
    (string | null)[]
  >,
) => number;

export const useUserConversation = (
  cid: string | null,
  refetchInterval?: RefetchInterval,
) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: async () => {
      const conversation = await OpenHands.getConversation(cid!);
      return conversation;
    },
    enabled: !!cid,
    retry: false,
    refetchInterval,
    staleTime: FIVE_MINUTES,
    gcTime: FIFTEEN_MINUTES,
  });
