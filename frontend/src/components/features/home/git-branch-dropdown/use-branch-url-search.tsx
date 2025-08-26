import { useState, useEffect } from "react";
import { Provider } from "#/types/settings";
import { Branch } from "#/types/git";

interface UseBranchUrlSearchOptions {
  inputValue: string;
  repository: string | null;
  provider: Provider;
  searchFunction: (repository: string, query: string, perPage?: number, selectedProvider?: Provider) => Promise<Branch[]>;
  urlPattern?: RegExp;
  extractQuery?: (url: string) => string | null;
}

export function useBranchUrlSearch({
  inputValue,
  repository,
  provider,
  searchFunction,
  urlPattern = /https:\/\/[^/]+\/([^/]+\/[^/]+)/,
  extractQuery = (url: string) => {
    const match = url.match(urlPattern);
    return match ? match[1] : null;
  },
}: UseBranchUrlSearchOptions) {
  const [urlSearchResults, setUrlSearchResults] = useState<Branch[]>([]);
  const [isUrlSearching, setIsUrlSearching] = useState(false);

  useEffect(() => {
    const performUrlSearch = async () => {
      if (!repository || !inputValue.trim()) {
        setUrlSearchResults([]);
        return;
      }

      const query = extractQuery(inputValue);
      if (!query) {
        setUrlSearchResults([]);
        return;
      }

      setIsUrlSearching(true);
      try {
        const results = await searchFunction(repository, query, 10, provider);
        setUrlSearchResults(results);
      } catch (error) {
        console.error("URL search failed:", error);
        setUrlSearchResults([]);
      } finally {
        setIsUrlSearching(false);
      }
    };

    const timeoutId = setTimeout(performUrlSearch, 300);
    return () => clearTimeout(timeoutId);
  }, [inputValue, repository, provider, searchFunction, extractQuery]);

  return {
    urlSearchResults,
    isUrlSearching,
  };
}