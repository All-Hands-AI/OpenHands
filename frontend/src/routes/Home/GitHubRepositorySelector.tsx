import React from "react";
import { useSubmit, Form } from "react-router-dom";

interface GitHubRepositorySelectorProps {
  repositories: GitHubRepository[];
}

export function GitHubRepositorySelector({
  repositories,
}: GitHubRepositorySelectorProps) {
  const submit = useSubmit();
  const [isFocused, setIsFocused] = React.useState(false);
  const [selectedRepo, setSelectedRepo] =
    React.useState<GitHubRepository | null>(null);

  const handleRepoSelection = (repo: GitHubRepository) => {
    setSelectedRepo(repo);
    setIsFocused(false);
    submit({ repo: repo.full_name }, { method: "get" });
  };

  return (
    <Form className="relative w-full">
      <input
        name="repo"
        type="text"
        className="text-sm w-full rounded-[4px] px-3 py-[10px] bg-[#525252] text-[#A3A3A3]"
        placeholder="Select a GitHub project"
        onFocus={() => setIsFocused(true)}
        defaultValue={selectedRepo?.full_name}
      />
      {isFocused && (
        <ul className="absolute">
          {repositories.map((repo) => (
            <li key={repo.id}>
              <button type="button" onClick={() => handleRepoSelection(repo)}>
                {repo.full_name}
              </button>
            </li>
          ))}
        </ul>
      )}
      <button type="submit" hidden aria-hidden />
    </Form>
  );
}
