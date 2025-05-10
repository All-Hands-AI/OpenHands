import { convertRawProvidersToList } from "#/utils/convert-raw-providers-to-list";
import { useSettings } from "./query/use-settings";

export const useUserProviders = () => {
  const { data: settings } = useSettings();
  return {
    providers: convertRawProvidersToList(settings?.PROVIDER_TOKENS_SET),
  };
};
