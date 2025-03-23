import { apiService } from "../api-service";
import { GetConfigResponse } from "../open-hands.types";

export const configApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    getConfig: builder.query<GetConfigResponse, void>({
      query: () => ({
        url: "/api/options/config",
        method: "GET",
      }),
      providesTags: ["Config"],
    }),
    getModels: builder.query<string[], void>({
      query: () => ({
        url: "/api/options/models",
        method: "GET",
      }),
      providesTags: ["Config"],
    }),
    getAgents: builder.query<string[], void>({
      query: () => ({
        url: "/api/options/agents",
        method: "GET",
      }),
      providesTags: ["Config"],
    }),
    getSecurityAnalyzers: builder.query<string[], void>({
      query: () => ({
        url: "/api/options/security-analyzers",
        method: "GET",
      }),
      providesTags: ["Config"],
    }),
  }),
});

export const {
  useGetConfigQuery,
  useGetModelsQuery,
  useGetAgentsQuery,
  useGetSecurityAnalyzersQuery,
} = configApiSlice;
