import { Autocomplete, AutocompleteItem } from "@nextui-org/react";
import React from "react";
import { useSubmit, Form } from "react-router-dom";

interface GitHubRepositorySelectorProps {
  repositories: GitHubRepository[];
}

export function GitHubRepositorySelector({
  repositories,
}: GitHubRepositorySelectorProps) {
  const submit = useSubmit();

  const handleRepoSelection = (id: string | null) => {
    const repo = repositories.find((r) => r.id.toString() === id);
    if (repo) {
      // set query param
      submit({ repo: repo.full_name }, { method: "get" });
    }
  };

  const handleClearSelection = () => {
    // clear query param
    submit({ repo: "" }, { method: "get" });
  };

  return (
    <Form className="relative w-full">
      <Autocomplete
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
          <AutocompleteItem key={repo.id} value={repo.id}>
            {repo.full_name}
          </AutocompleteItem>
        ))}
      </Autocomplete>
    </Form>
  );
}
