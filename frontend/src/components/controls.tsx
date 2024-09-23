import { IoLockClosed } from "react-icons/io5";
import { useRouteLoaderData } from "@remix-run/react";
import React from "react";
import { useSelector } from "react-redux";
import AgentControlBar from "./AgentControlBar";
import AgentStatusBar from "./AgentStatusBar";
import { ProjectMenuCard } from "./project-menu/ProjectMenuCard";
import { clientLoader as rootClientLoader } from "#/root";
import { RootState } from "#/store";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const { selectedRepository } = useSelector(
    (state: RootState) => state.initalQuery,
  );
  const rootData = useRouteLoaderData<typeof rootClientLoader>("root");

  const projectMenuCardData = React.useMemo(
    () =>
      rootData?.user && selectedRepository
        ? {
            avatar: rootData.user.avatar_url,
            repoName: selectedRepository,
            lastCommit: { id: "123", date: "2021-10-10" },
          }
        : null,
    [rootData, selectedRepository],
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
        token={rootData?.ghToken ?? null}
        githubData={projectMenuCardData}
      />
    </div>
  );
}
