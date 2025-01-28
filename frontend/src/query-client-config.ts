import { QueryClientConfig, QueryCache } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import toast from "react-hot-toast";

const QUERY_KEYS_TO_IGNORE = ["authenticated", "hosts"];

export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!QUERY_KEYS_TO_IGNORE.some((key) => query.queryKey.includes(key))) {
        let errorMessage: string | null = null;

        if (isAxiosError(error)) {
          console.warn(error.response?.data);

          if (typeof error.response?.data === "string") {
            errorMessage = error.response?.data;
          } else if (error.response?.data.message) {
            errorMessage = error.response?.data.message;
          } else {
            errorMessage = error.message;
          }
        } else {
          errorMessage = error.message;
        }

        toast.error(errorMessage || "An error occurred");
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
