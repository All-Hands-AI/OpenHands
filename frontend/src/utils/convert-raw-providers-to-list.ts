import { Provider } from "#/types/settings";

export const convertRawProvidersToList = (
  raw: Partial<Record<Provider, string | null>> | undefined,
): Provider[] => {
  if (!raw) return [];
  const list: Provider[] = [];
  for (const [key, value] of Object.entries(raw)) {
    if (value) {
      list.push(key as Provider);
    }
  }
  return list;
};
