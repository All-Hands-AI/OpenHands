import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Provider } from "#/types/settings";
import { useAppInstallations } from "./use-app-installations";
import { useBitbucketWorkspaces } from "./use-bitbucket-workspaces";

export const useUserRepositories = (provider?: Provider, page = 1) => {
  const [currentPage, setCurrentPage] = useState(page);
  const { data: githubInstallations } = useAppInstallations();
  const { data: bitbucketWorkspaces } = useBitbucketWorkspaces();

  // Track the current installation/workspace being used
  const [currentInstallationId, setCurrentInstallationId] = useState<
    string | undefined
  >();
  const [currentWorkspace, setCurrentWorkspace] = useState<
    string | undefined
  >();

  // Set the first installation/workspace when data is loaded
  useEffect(() => {
    if (
      provider === "github" &&
      githubInstallations?.length &&
      !currentInstallationId
    ) {
      setCurrentInstallationId(githubInstallations[0]);
    } else if (
      provider === "bitbucket" &&
      bitbucketWorkspaces?.length &&
      !currentWorkspace
    ) {
      setCurrentWorkspace(bitbucketWorkspaces[0]);
    }
  }, [
    provider,
    githubInstallations,
    bitbucketWorkspaces,
    currentInstallationId,
    currentWorkspace,
  ]);

  // Reset page when provider changes
  useEffect(() => {
    setCurrentPage(1);
  }, [provider]);

  return {
    ...useQuery({
      queryKey: [
        "repositories",
        provider,
        currentInstallationId,
        currentWorkspace,
        currentPage,
      ],
      queryFn: () =>
        OpenHands.retrieveUserGitRepositories(
          provider,
          currentInstallationId,
          currentWorkspace,
          currentPage,
        ),
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 15, // 15 minutes
      enabled:
        !provider ||
        (provider === "github" && !!currentInstallationId) ||
        (provider === "bitbucket" && !!currentWorkspace) ||
        provider === "gitlab",
    }),
    currentPage,
    setCurrentPage,
    githubInstallations,
    bitbucketWorkspaces,
    currentInstallationId,
    setCurrentInstallationId,
    currentWorkspace,
    setCurrentWorkspace,
  };
};
