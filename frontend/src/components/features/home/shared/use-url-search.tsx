import { useState, useEffect } from "react";
import { Provider } from "#/types/settings";

interface UseUrlSearchOptions<T> {
  inputValue: string;
  provider: Provider;
  searchFunction: (query: string, limit: number, provider: Provider) => Promise<T[]>;
  urlPattern?: RegExp;
  extractQuery?: (url: string) => string | null;
}

export function useUrlSearch<T>({
  inputValue,
  provider,
  searchFunction,
  urlPattern = /https:\/\/[^/]+\/([^/]+\/[^/]+)/,
  extractQuery = (url: string) => {
    const match = url.match(urlPattern);
    return match ? match[1] : null;
  },
}: UseUrlSearchOptions<T>) {
  const [urlSearchResults, setUrlSearchResults] = useState<T[]>([]);
  const [isUrlSearchLoading, setIsUrlSearchLoading] = useState(false);

  useEffect(() => {
    const handleUrlSearch = async () => {
      if (inputValue.startsWith("https://")) {
        const query = extractQuery(inputValue);
        if (query) {
          console.log("URL detected, searching for:", query);
          setIsUrlSearchLoading(true);
          try {
            const results = await searchFunction(query, 3, provider);
            console.log("URL search results:", results);
            setUrlSearchResults(results);
          } catch (error) {
            console.error("URL search failed:", error);
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
  }, [inputValue, provider, searchFunction, extractQuery]);

  return { urlSearchResults, isUrlSearchLoading };
}