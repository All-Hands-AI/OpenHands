import { createApi } from "@reduxjs/toolkit/query/react";
import { openHands } from "./open-hands-axios";
import { retrieveAxiosErrorMessage } from "../utils/retrieve-axios-error-message";
import { displayErrorToast } from "../utils/custom-toast-handlers";

// Define the types for the query parameters
interface QueryParams {
  url: string;
  method: string;
  data?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
}

// Create a custom base query that uses the existing axios instance
const axiosBaseQuery =
  () =>
  async ({ url, method, data, params }: QueryParams) => {
    try {
      const result = await openHands({
        url,
        method,
        data,
        params,
      });
      return { data: result.data };
    } catch (error: unknown) {
      // Type guard for error
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as {
          response?: {
            status?: number;
            data?: unknown;
          };
          message?: string;
        };

        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage || "An error occurred");

        return {
          error: {
            status: axiosError.response?.status,
            data: axiosError.response?.data || axiosError.message,
          },
        };
      }

      // Fallback for non-axios errors
      displayErrorToast("An unexpected error occurred");
      return {
        error: {
          status: 500,
          data: "Unknown error",
        },
      };
    }
  };

// Create the API service
export const apiService = createApi({
  reducerPath: "api",
  baseQuery: axiosBaseQuery(),
  tagTypes: [
    "Config",
    "Files",
    "File",
    "User",
    "Conversations",
    "Conversation",
    "Settings",
    "Balance",
    "VSCodeUrl",
    "Repositories",
    "Installations",
    "Policy",
    "RiskSeverity",
    "Traces",
    "ActiveHost",
  ],
  endpoints: () => ({}),
});
