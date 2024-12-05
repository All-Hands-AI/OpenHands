import axios, { InternalAxiosRequestConfig } from "axios";
import { ErrorResponse, FileUploadSuccessResponse } from "./open-hands.types";

export const isOpenHandsErrorResponse = (
  data: ErrorResponse | FileUploadSuccessResponse,
): data is ErrorResponse =>
  typeof data === "object" && data !== null && "error" in data;

export const createAxiosError = (
  message: string,
  config: InternalAxiosRequestConfig<any>,
  status: any,
  headers: any,
) => {
  const error = new axios.AxiosError(
    message, // Error message
    undefined, // Error code
    config, // Config
    undefined,
    {
      data: {},
      status: status || -1,
      statusText: "",
      headers,
      config,
    }, // Request (optional)
  );
};
