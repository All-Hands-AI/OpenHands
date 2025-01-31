import { AxiosError } from "axios";
import { isAxiosErrorWithResponse } from "./type-guards";

/**
 * Retrieve the error message from an Axios error
 * @param error The error to render a toast for
 */
export const retrieveAxiosErrorMessage = (error: AxiosError) => {
  let errorMessage: string | null = null;

  if (isAxiosErrorWithResponse(error) && error.response?.data.error) {
    errorMessage = error.response?.data.error;
  } else {
    errorMessage = error.message;
  }

  return errorMessage || "An error occurred";
};
