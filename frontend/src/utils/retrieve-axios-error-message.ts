import { AxiosError } from "axios";
import {
  isAxiosErrorWithErrorField,
  isAxiosErrorWithMessageField,
} from "@openhands/types";

/**
 * Retrieve the error message from an Axios error
 * @param error The error to render a toast for
 */
export const retrieveAxiosErrorMessage = (error: AxiosError): string => {
  if (isAxiosErrorWithErrorField(error) && error.response?.data.error) {
    return error.response.data.error;
  }

  if (isAxiosErrorWithMessageField(error) && error.response?.data.message) {
    return error.response.data.message;
  }

  return error.message;
};
