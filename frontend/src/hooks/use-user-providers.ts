import React from "react";
import { convertRawProvidersToList } from "#/utils/convert-raw-providers-to-list";
import { useSettings } from "./query/use-settings";

export const useUserProviders = () => {
  const { data: settings, isLoading: isLoadingSettings } = useSettings();

  const providers = React.useMemo(
    () => convertRawProvidersToList(settings?.PROVIDER_TOKENS_SET),
    [settings?.PROVIDER_TOKENS_SET],
  );

  return {
    providers,
    isLoadingSettings,
  };
};
