import { AxiosError } from "axios";
import toast from "react-hot-toast";
import { isAxiosErrorWithResponse } from "./type-guards";

/**
 * Renders a toast with the error message from an Axios error
 * @param error The error to render a toast for
 */
export const renderToastIfError = (error: AxiosError) => {
  let errorMessage: string | null = null;

  if (isAxiosErrorWithResponse(error) && error.response?.data.error) {
    errorMessage = error.response?.data.error;
  } else {
    errorMessage = error.message;
  }

  toast.error(errorMessage || "An error occurred");
};
