import { useQuery } from "@tanstack/react-query";

const authenticateUserQueryFn = async (gitHubToken: string) => {
  if (window.__APP_MODE__ === "oss") return true;

  const response = await fetch("/api/authenticate", {
    method: "POST",
    headers: {
      "X-GitHub-Token": gitHubToken,
    },
  });

  return response.ok;
};

interface UseIsAuthedConfig {
  gitHubToken: string | null;
}

export const useIsAuthed = ({ gitHubToken }: UseIsAuthedConfig) =>
  useQuery({
    queryKey: ["user", "authenticated", gitHubToken],
    queryFn: () => authenticateUserQueryFn(gitHubToken || ""),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
