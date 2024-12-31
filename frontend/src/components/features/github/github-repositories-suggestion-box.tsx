import React from "react";
import { SuggestionBox } from "#/components/features/suggestions/suggestion-box";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import { GitHubRepositorySelector } from "./github-repo-selector";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { ConnectToGitHubModal } from "#/components/shared/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { isGitHubErrorReponse } from "#/api/github-axios-instance";

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
