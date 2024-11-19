import { useQuery } from "@tanstack/react-query";

interface UseListFilesConfig {
  token: string | null;
  path?: string;
  enabled?: boolean;
}

const getFilesQueryFn = async (
  token: UseListFilesConfig["token"],
  path: UseListFilesConfig["path"],
): Promise<string[]> => {
  const url = new URL("/api/list-files", window.location.origin);
  if (path) url.searchParams.append("path", path);
  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch files");
  }

  return response.json();
};

export const useGetFiles = (config: UseListFilesConfig) =>
  useQuery({
    queryKey: ["files", config.token, config.path],
    queryFn: () => getFilesQueryFn(config.token, config.path),
    enabled: config.enabled && !!config.token,
  });
