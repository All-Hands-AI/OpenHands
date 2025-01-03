import React from "react";
import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import { setSelectedRepository } from "#/state/initial-query-slice";
import { useConfig } from "#/hooks/query/use-config";

interface GitHubRepositoryWithPublic extends GitHubRepository {
  is_public?: boolean;
}

interface GitHubRepositorySelectorProps {
  onInputChange: (value: string) => void;
  onSelect: () => void;
  repositories: GitHubRepositoryWithPublic[];
}

export function GitHubRepositorySelector({
  onInputChange,
  onSelect,
  repositories,
}: GitHubRepositorySelectorProps) {
  const { data: config } = useConfig();
  const [selectedKey, setSelectedKey] = React.useState<string | null>(null);

  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = repositories.find((r) => r.id.toString() === id);
    if (!repo) return;

    if (repo.id === -1000) {
      window.open(
        `https://github.com/apps/${config?.APP_SLUG}/installations/new`,
        "_blank",
      );
      return;
    }

    dispatch(setSelectedRepository(repo.full_name));
    posthog.capture("repository_selected");
    onSelect();
    setSelectedKey(id);
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
      selectedKey={selectedKey}
      items={repositories}
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      onInputChange={onInputChange}
      clearButtonProps={{ onPress: handleClearSelection }}
      listboxProps={{
        emptyContent,
      }}
    >
      {(item) => (
        <AutocompleteItem
          data-testid="github-repo-item"
          key={item.id}
          value={item.id}
          textValue={item.full_name}
        >
          <div className="flex items-center justify-between">
            {item.full_name}
            {item.is_public && !!item.stargazers_count && (
              <span className="text-xs text-gray-400">
                ({item.stargazers_count}⭐)
              </span>
            )}
          </div>
        </AutocompleteItem>
      )}
    </Autocomplete>
  );
}
