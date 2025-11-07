import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import { useShouldShowUserFeatures } from "#/hooks/use-should-show-user-features";
import { openHands } from "#/api/open-hands-axios";

/**
 * Hook to fetch the Keycloak user ID for PostHog aliasing
 * Only active in SaaS mode
 */
export const useKeycloakId = () => {
  const { data: config } = useConfig();
  const shouldFetchUser = useShouldShowUserFeatures();

  return useQuery({
    queryKey: ["keycloak-id"],
    queryFn: async () => {
      const response = await openHands.get<{ keycloak_user_id: string | null }>(
        "/api/user/keycloak-id",
      );
      return response.data.keycloak_user_id;
    },
    enabled: shouldFetchUser && config?.APP_MODE === "saas",
    retry: false,
    staleTime: 1000 * 60 * 60, // 1 hour (doesn't change often)
  });
};
