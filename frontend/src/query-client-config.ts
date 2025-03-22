import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";
import { displayErrorToast } from "./utils/custom-toast-handlers";

const shownErrors = new Set<string>();
export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Don't show error toasts on the logout page
      if (window.location.pathname.includes('/logout')) {
        return;
      }

      if (!query.meta?.disableToast) {
        const errorMessage = retrieveAxiosErrorMessage(error);

        if (!shownErrors.has(errorMessage)) {
          displayErrorToast(errorMessage || "An error occurred");
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
      // Don't show error toasts on the logout page
      if (window.location.pathname.includes('/logout')) {
        return;
      }

      if (!mutation?.meta?.disableToast) {
        const message = retrieveAxiosErrorMessage(error);
        displayErrorToast(message);
      }
    },
  }),
};
