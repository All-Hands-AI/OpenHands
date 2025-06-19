import { convertRawProvidersToList } from "#/utils/convert-raw-providers-to-list";
import React from "react";
import { useSettings } from "./query/use-settings";

export const useUserProviders = () => {
  const { data: settings } = useSettings();

  const providers = React.useMemo(
    () => convertRawProvidersToList(settings?.PROVIDER_TOKENS_SET),
    [settings?.PROVIDER_TOKENS_SET],
  );

  return {
    providers: convertRawProvidersToList(settings?.PROVIDER_TOKENS_SET),
  };
};
