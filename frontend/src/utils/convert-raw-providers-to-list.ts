import { Provider, ProviderTokenSettings } from "#/types/settings";

export const convertRawProvidersToList = (
  raw: Partial<Record<Provider, ProviderTokenSettings | null>> | undefined,
): Provider[] => {
  if (!raw) return [];
  const list: Provider[] = [];
  for (const key of Object.keys(raw)) {
    const providerValue = raw[key as Provider];
    if (key && providerValue) {
      list.push(key as Provider);
    }
  }
  return list;
};
