import { useState, useEffect } from "react";
import { Provider } from "#/types/settings";
import { GitRepository } from "#/types/git";
import OpenHands from "#/api/open-hands";

export function useUrlSearch(inputValue: string, provider: Provider) {
  const [urlSearchResults, setUrlSearchResults] = useState<GitRepository[]>([]);
  const [isUrlSearchLoading, setIsUrlSearchLoading] = useState(false);

  useEffect(() => {
    const handleUrlSearch = async () => {
      if (inputValue.startsWith("https://")) {
        const match = inputValue.match(/https:\/\/[^/]+\/([^/]+\/[^/]+)/);
        if (match) {
          const repoName = match[1];

          setIsUrlSearchLoading(true);
          try {
            const repositories = await OpenHands.searchGitRepositories(
              repoName,
              3,
              provider,
            );

            setUrlSearchResults(repositories);
          } catch (error) {
            setUrlSearchResults([]);
          } finally {
            setIsUrlSearchLoading(false);
          }
        }
      } else {
        setUrlSearchResults([]);
      }
    };

    handleUrlSearch();
  }, [inputValue, provider]);

  return { urlSearchResults, isUrlSearchLoading };
}
