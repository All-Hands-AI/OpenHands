import { IoLockClosed } from "react-icons/io5";
import React from "react";
import AgentControlBar from "./AgentControlBar";
import AgentStatusBar from "./AgentStatusBar";
import { ProjectMenuCard } from "./project-menu/ProjectMenuCard";
import { getGitHubToken } from "#/services/auth";

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
  const ghToken = getGitHubToken();
  const repo = localStorage.getItem("repo");

  const projectMenuCardData = React.useMemo(
    () =>
      repo && lastCommitData
        ? {
            repoName: repo,
            lastCommit: lastCommitData,
            avatar: null, // TODO: fetch repo avatar
          }
        : null,
    [repo, lastCommitData],
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
