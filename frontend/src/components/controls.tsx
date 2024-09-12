import { IoLockClosed } from "react-icons/io5";
import { useRouteLoaderData } from "@remix-run/react";
import AgentControlBar from "./AgentControlBar";
import AgentStatusBar from "./AgentStatusBar";
import { ProjectMenuCard } from "./project-menu/ProjectMenuCard";
import VolumeIcon from "./VolumeIcon";
import { clientLoader as rootClientLoader } from "#/root";
import { clientLoader as appClientLoader } from "#/routes/app";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const rootData = useRouteLoaderData<typeof rootClientLoader>("root");
  const appData = useRouteLoaderData<typeof appClientLoader>("routes/app");

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />
      </div>

      <div style={{ display: "flex", alignItems: "center" }}>
        <div style={{ marginRight: "8px" }}>
          <VolumeIcon />
        </div>
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
        githubData={
          rootData?.user && appData?.repo
            ? {
                avatar: rootData.user.avatar_url,
                repoName: appData.repo,
                lastCommit: { id: "123", date: "2021-10-10" },
              }
            : null
        }
      />
    </div>
  );
}
