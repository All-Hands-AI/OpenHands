import { FaBitbucket, FaGithub, FaGitlab } from "react-icons/fa6";
import { RepositorySelection } from "#/api/open-hands.types";

interface ConversationRepoLinkProps {
  selectedRepository: RepositorySelection;
  variant: "compact" | "default";
}

export function ConversationRepoLink({
  selectedRepository,
  variant = "default",
}: ConversationRepoLinkProps) {
  if (variant === "compact") {
    return (
      <span
        data-testid="conversation-card-selected-repository"
        className="text-xs text-neutral-400"
      >
        {selectedRepository.selected_repository}
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1">
      {selectedRepository.git_provider === "github" && <FaGithub size={14} />}
      {selectedRepository.git_provider === "gitlab" && <FaGitlab />}
      {selectedRepository.git_provider === "bitbucket" && <FaBitbucket />}

      <span
        data-testid="conversation-card-selected-repository"
        className="text-xs text-neutral-400"
      >
        {selectedRepository.selected_repository}
      </span>
      <code
        data-testid="conversation-card-selected-branch"
        className="text-xs text-neutral-400 border border-neutral-700 rounded px-1 py-0.5 w-fit bg-neutral-800"
      >
        {selectedRepository.selected_branch}
      </code>
    </div>
  );
}
