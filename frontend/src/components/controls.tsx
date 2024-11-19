import { IoLockClosed } from "react-icons/io5";
import React from "react";
import AgentControlBar from "./AgentControlBar";
import AgentStatusBar from "./AgentStatusBar";
import { ProjectMenuCard } from "./project-menu/ProjectMenuCard";
import { useGitHubUser } from "#/hooks/query/use-github-user";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
  lastCommitData: GitHubCommit | null;
}

export function Controls({
  setSecurityOpen,
  showSecurityLock,
  lastCommitData,
}: ControlsProps) {
  const ghToken = localStorage.getItem("ghToken");
  const repo = localStorage.getItem("repo");

  const { data: user } = useGitHubUser(ghToken);

  const projectMenuCardData = React.useMemo(
    () =>
      user && repo && lastCommitData
        ? {
            avatar: user.avatar_url,
            repoName: repo,
            lastCommit: lastCommitData,
          }
        : null,
    [user, repo, lastCommitData],
  );

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <div
            className="cursor-pointer hover:opacity-80 transition-all"
            style={{ marginRight: "8px" }}
            onClick={() => setSecurityOpen(true)}
          >
            <IoLockClosed size={20} />
          </div>
        )}
      </div>

      <ProjectMenuCard
        isConnectedToGitHub={!!ghToken}
        githubData={projectMenuCardData}
      />
    </div>
  );
}
