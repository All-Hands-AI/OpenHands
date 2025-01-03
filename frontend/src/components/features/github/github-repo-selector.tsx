import React from "react";
import {
  Autocomplete,
  AutocompleteItem,
  AutocompleteSection,
} from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";
import { sanitizeQuery } from "#/utils/sanitize-query";

interface GitHubRepositorySelectorProps {
  onInputChange: (value: string) => void;
  onSelect: () => void;
  userRepositories: GitHubRepository[];
  publicRepositories: GitHubRepository[];
}

export function GitHubRepositorySelector({
  onInputChange,
  onSelect,
  userRepositories,
  publicRepositories,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);

  const allRepositories: GitHubRepository[] = [
    ...publicRepositories.filter(
      (repo) => !publicRepositories.find((r) => r.id === repo.id),
    ),
    ...userRepositories,
  ];

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = allRepositories.find((r) => r.id.toString() === id);
    if (repo) {
      dispatch(setSelectedRepository(repo.full_name));
      posthog.capture("repository_selected");
      onSelect();
      setSelectedKey(id);
    }
  };

  const handleClearSelection = () => {
    dispatch(setSelectedRepository(null));
  };

  const emptyContent = "No results found.";

  return (
    <Autocomplete
      data-testid="github-repo-selector"
      name="repo"
      aria-label="GitHub Repository"
      placeholder="Select a GitHub project"
      isVirtualized={false}
      selectedKey={selectedKey}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      onInputChange={onInputChange}
      clearButtonProps={{ onClick: handleClearSelection }}
      listboxProps={{
        emptyContent,
      }}
      defaultFilter={(textValue, inputValue) =>
        !inputValue ||
        sanitizeQuery(textValue).includes(sanitizeQuery(inputValue))
      }
    >
      {config?.APP_MODE === "saas" &&
        config?.APP_SLUG &&
        ((
          <AutocompleteItem key="install">
            <a
              href={`https://github.com/apps/${config.APP_SLUG}/installations/new`}
              target="_blank"
              rel="noreferrer noopener"
              onClick={(e) => e.stopPropagation()}
            >
              Add more repositories...
            </a>
          </AutocompleteItem> // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ) as any)}
      {userRepositories.length > 0 && (
        <AutocompleteSection showDivider title="Your Repos">
          {userRepositories.map((repo) => (
            <AutocompleteItem
              data-testid="github-repo-item"
              key={repo.id}
              value={repo.id}
              className="data-[selected=true]:bg-default-100"
              textValue={repo.full_name}
            >
              {repo.full_name}
            </AutocompleteItem>
          ))}
        </AutocompleteSection>
      )}
      {publicRepositories.length > 0 && (
        <AutocompleteSection showDivider title="Public Repos">
          {publicRepositories.map((repo) => (
            <AutocompleteItem
              data-testid="github-repo-item"
              key={repo.id}
              value={repo.id}
              className="data-[selected=true]:bg-default-100"
              textValue={repo.full_name}
            >
              {repo.full_name}
              <span className="ml-1 text-gray-400">
                ({repo.stargazers_count || 0}⭐)
              </span>
            </AutocompleteItem>
          ))}
        </AutocompleteSection>
      )}
    </Autocomplete>
  );
}
