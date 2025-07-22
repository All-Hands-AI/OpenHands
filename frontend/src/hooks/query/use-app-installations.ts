import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import { useIsAuthed } from "./use-is-authed";
import OpenHands from "#/api/open-hands";
import { useUserProviders } from "../use-user-providers";
import { Provider } from "#/types/settings";

export const useAppInstallations = (provider: Provider | null) => {
  const { data: config } = useConfig();
  const { data: userIsAuthenticated } = useIsAuthed();
  const { providers } = useUserProviders();

  return useQuery({
    queryKey: ["installations", providers, provider],
    queryFn: () => OpenHands.getUserInstallationIds(provider!),
    enabled:
      userIsAuthenticated &&
      !!provider &&
      (providers.includes("github") || providers.includes("bitbucket")) &&
      !!config?.GITHUB_CLIENT_ID &&
      config?.APP_MODE === "saas",
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
