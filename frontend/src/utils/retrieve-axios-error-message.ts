import { AxiosError } from "axios";
import {
  isAxiosErrorWithErrorField,
  isAxiosErrorWithMessageField,
} from "./type-guards";

/**
 * Retrieve the error message from an Axios error
 * @param error The error to render a toast for
 * @param t Translation function
 */
export const retrieveAxiosErrorMessage = (
  error: AxiosError,
  t: (key: string) => string,
) => {
  let errorMessage: string | null = null;

  if (isAxiosErrorWithErrorField(error) && error.response?.data.error) {
    errorMessage = error.response?.data.error;
  } else if (
    isAxiosErrorWithMessageField(error) &&
    error.response?.data.message
  ) {
    errorMessage = error.response?.data.message;
  } else {
    errorMessage = error.message;
  }

  return errorMessage || t("ERROR$GENERIC");
};
