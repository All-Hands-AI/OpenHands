import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import toast from "react-hot-toast";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";

const shownErrors = new Set<string>();
export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!query.meta?.disableToast) {
        const errorMessage = retrieveAxiosErrorMessage(error);

        if (!shownErrors.has(errorMessage)) {
          toast.error(errorMessage || "An error occurred");
          shownErrors.add(errorMessage);

          setTimeout(() => {
            shownErrors.delete(errorMessage);
          }, 3000);
        }
      }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _, __, mutation) => {
      if (!mutation?.meta?.disableToast) {
        const message = retrieveAxiosErrorMessage(error);
        toast.error(message);
      }
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 15, // 15 minutes
    },
  },
};
