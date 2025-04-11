import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import i18next from "i18next";
import { I18nKey } from "./i18n/declaration";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";
import { displayErrorToast } from "./utils/custom-toast-handlers";

const shownErrors = new Set<string>();
export const queryClientConfig: QueryClientConfig = {
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!query.meta?.disableToast) {
        const errorMessage = retrieveAxiosErrorMessage(error);

        if (!shownErrors.has(errorMessage || "")) {
          displayErrorToast(errorMessage || i18next.t(I18nKey.ERROR$GENERIC));
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
        displayErrorToast(message || i18next.t(I18nKey.ERROR$GENERIC));
      }
    },
  }),
};
