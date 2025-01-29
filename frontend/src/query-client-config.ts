import { QueryClientConfig, QueryCache } from "@tanstack/react-query";
import { renderToastIfError } from "./utils/render-toast-if-error";

const QUERY_KEYS_TO_IGNORE = ["authenticated", "hosts"];

export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!QUERY_KEYS_TO_IGNORE.some((key) => query.queryKey.includes(key))) {
        renderToastIfError(error);
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
        renderToastIfError(error);
      },
    },
  },
};
