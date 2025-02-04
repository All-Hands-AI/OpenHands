import { AxiosError } from "axios";

export const isAxiosErrorWithResponse = (
  error: AxiosError,
): error is AxiosError<{ error: string }> =>
  typeof error.response?.data === "object" &&
  error.response?.data !== null &&
  "error" in error.response.data &&
  typeof error.response?.data?.error === "string";
