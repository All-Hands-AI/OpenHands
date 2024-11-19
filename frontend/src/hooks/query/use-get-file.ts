import { useQuery } from "@tanstack/react-query";

interface UseGetFileConfig {
  token: string | null;
  path: string;
}

const getFileQueryFn = async (
  token: UseGetFileConfig["token"],
  path: UseGetFileConfig["path"],
): Promise<string> => {
  const url = new URL("/api/select-file", window.location.origin);
  url.searchParams.append("file", path);

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch file");
  }

  const data = await response.json();
  return data.code;
};

export const useGetFile = (config: UseGetFileConfig) =>
  useQuery({
    queryKey: ["file", config.token, config.path],
    queryFn: () => getFileQueryFn(config.token, config.path),
    enabled: false,
  });
