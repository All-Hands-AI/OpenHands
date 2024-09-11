import React from "react";
import { useRouteLoaderData } from "@remix-run/react";
import EllipsisH from "#/assets/ellipsis-h.svg?react";
import CloudConnection from "#/assets/cloud-connection.svg?react";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ModalBackdrop } from "../modals/modal-backdrop";
import { ConnectToGitHubModal } from "../modals/connect-to-github-modal";
import { cn } from "#/utils/utils";
import { clientLoader } from "#/routes/app";

export function ProjectMenuCard() {
  const data = useRouteLoaderData<typeof clientLoader>("routes/app");
  const [menuIsOpen, setMenuIsOpen] = React.useState(false);
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);

  const toggleMenuVisibility = () => {
    setMenuIsOpen((prev) => !prev);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {menuIsOpen && (
        <ContextMenu className="absolute right-0 bottom-[calc(100%+8px)]">
          <ContextMenuListItem
            onClick={() => setConnectToGitHubModalOpen(true)}
          >
            {data?.ghToken ? "Connected" : "Connect"} to GitHub
          </ContextMenuListItem>
          <ContextMenuListItem>Reset Workspace</ContextMenuListItem>
          <ContextMenuListItem>Download as .zip</ContextMenuListItem>
        </ContextMenu>
      )}
      <div className="flex flex-col">
        <span className="text-sm leading-6 font-semibold">New Project</span>
        <button type="button" onClick={() => setConnectToGitHubModalOpen(true)}>
          <span
            className={cn(
              "text-xs leading-4 text-[#A3A3A3] flex items-center gap-2",
              "hover:underline hover:underline-offset-2",
            )}
          >
            {data?.ghToken ? "Connected" : "Connect"} to GitHub
            <CloudConnection width={12} height={12} />
          </span>
        </button>
      </div>
      <button
        type="button"
        onClick={toggleMenuVisibility}
        aria-label="Open project menu"
      >
        <EllipsisH width={36} height={36} />
      </button>
      {connectToGitHubModalOpen && (
        <ModalBackdrop>
          <ConnectToGitHubModal
            onClose={() => setConnectToGitHubModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </div>
  );
}
