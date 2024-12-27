import React from "react";
import { useSelector } from "react-redux";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { ProjectMenuCard } from "../project-menu/ProjectMenuCard";
import { useAuth } from "#/context/auth-context";
import { RootState } from "#/store";
import { SecurityLock } from "./security-lock";

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
  const { gitHubToken } = useAuth();
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const projectMenuCardData = React.useMemo(
    () =>
      selectedRepository && lastCommitData
        ? {
            repoName: selectedRepository,
            lastCommit: lastCommitData,
            avatar: null, // TODO: fetch repo avatar
          }
        : null,
    [selectedRepository, lastCommitData],
  );

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>

      <ProjectMenuCard
        isConnectedToGitHub={!!gitHubToken}
        githubData={projectMenuCardData}
      />
    </div>
  );
}
