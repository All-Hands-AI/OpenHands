import { QueryClientConfig, QueryCache } from "@tanstack/react-query";
import toast from "react-hot-toast";

const QUERY_KEYS_TO_IGNORE = ["authenticated", "hosts"];

export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!QUERY_KEYS_TO_IGNORE.some((key) => query.queryKey.includes(key))) {
        toast.error(error.message);
      }
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 15, // 15 minutes
    },
    mutations: {
      onError: (error) => {
        toast.error(error.message);
      },
    },
  },
};
