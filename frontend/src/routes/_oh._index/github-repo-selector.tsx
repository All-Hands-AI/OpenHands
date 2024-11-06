import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { setSelectedRepository } from "#/state/initial-query-slice";

interface GitHubRepositorySelectorProps {
  repositories: GitHubRepository[];
}

export function GitHubRepositorySelector({
  repositories,
}: GitHubRepositorySelectorProps) {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleRepoSelection = (id: string | null) => {
    const repo = repositories.find((r) => r.id.toString() === id);
    if (repo) {
      // set query param
      dispatch(setSelectedRepository(repo.full_name));
      navigate("/app");
    }
  };

  const handleClearSelection = () => {
    // clear query param
    dispatch(setSelectedRepository(null));
  };

  return (
    <Autocomplete
      data-testid="github-repo-selector"
      name="repo"
      aria-label="GitHub Repository"
      placeholder="Select a GitHub project"
      inputProps={{
        classNames: {
          inputWrapper:
            "text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]",
        },
      }}
      onSelectionChange={(id) => handleRepoSelection(id?.toString() ?? null)}
      clearButtonProps={{ onClick: handleClearSelection }}
    >
      {repositories.map((repo) => (
        <AutocompleteItem
          data-testid="github-repo-item"
          key={repo.id}
          value={repo.id}
        >
          {repo.full_name}
        </AutocompleteItem>
      ))}
    </Autocomplete>
  );
}
