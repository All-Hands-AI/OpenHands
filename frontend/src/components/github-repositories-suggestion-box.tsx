import React from "react";
import { isGitHubErrorReponse } from "#/api/github";
import { SuggestionBox } from "#/routes/_oh._index/suggestion-box";
import { ConnectToGitHubModal } from "./modals/connect-to-github-modal";
import { ModalBackdrop } from "./modals/modal-backdrop";
import { GitHubRepositorySelector } from "#/routes/_oh._index/github-repo-selector";
import ModalButton from "./buttons/modal-button";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";

interface GitHubRepositoriesSuggestionBoxProps {
  handleSubmit: () => void;
  repositories: GitHubRepository[];
  gitHubAuthUrl: string | null;
  user: GitHubErrorReponse | GitHubUser | null;
}

export function GitHubRepositoriesSuggestionBox({
  handleSubmit,
  repositories,
  gitHubAuthUrl,
  user,
}: GitHubRepositoriesSuggestionBoxProps) {
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);

  const handleConnectToGitHub = () => {
    if (gitHubAuthUrl) {
      window.location.href = gitHubAuthUrl;
    } else {
      setConnectToGitHubModalOpen(true);
    }
  };

  if (isGitHubErrorReponse(repositories)) {
    return (
      <SuggestionBox
        title="Error Fetching Repositories"
        content={
          <p className="text-danger text-center">{repositories.message}</p>
        }
      />
    );
  }

  const isLoggedIn = !!user && !isGitHubErrorReponse(user);

  return (
    <>
      <SuggestionBox
        title="Open a Repo"
        content={
          isLoggedIn ? (
            <GitHubRepositorySelector
              onSelect={handleSubmit}
              repositories={repositories}
            />
          ) : (
            <ModalButton
              text="Connect to GitHub"
              icon={<GitHubLogo width={20} height={20} />}
              className="bg-[#791B80] w-full"
              onClick={handleConnectToGitHub}
            />
          )
        }
      />
      {connectToGitHubModalOpen && (
        <ModalBackdrop onClose={() => setConnectToGitHubModalOpen(false)}>
          <ConnectToGitHubModal
            onClose={() => setConnectToGitHubModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </>
  );
}
