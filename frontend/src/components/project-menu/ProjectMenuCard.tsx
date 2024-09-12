import React from "react";
import EllipsisH from "#/assets/ellipsis-h.svg?react";
import CloudConnection from "#/assets/cloud-connection.svg?react";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ModalBackdrop } from "../modals/modal-backdrop";
import { ConnectToGitHubModal } from "../modals/connect-to-github-modal";
import { cn } from "#/utils/utils";
import ExternalLinkIcon from "#/assets/external-link.svg?react";

// TODO: Merge the two component variants into one

function EmptyProjectMenuCard() {
  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);

  const toggleMenuVisibility = () => {
    setContextMenuIsOpen((prev) => !prev);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {contextMenuIsOpen && (
        <ContextMenu className="absolute right-0 bottom-[calc(100%+8px)]">
          <ContextMenuListItem
            onClick={() => setConnectToGitHubModalOpen(true)}
          >
            Connect to GitHub
          </ContextMenuListItem>
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
            Connect to GitHub
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

interface DetailedProjectMenuCardProps {
  avatar: string;
  repoName: string;
  lastCommit: { id: string; date: string };
}

function DetailedProjectMenuCard({
  avatar,
  repoName,
  lastCommit,
}: DetailedProjectMenuCardProps) {
  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);

  const toggleMenuVisibility = () => {
    setContextMenuIsOpen((prev) => !prev);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {contextMenuIsOpen && (
        <ContextMenu className="absolute right-0 bottom-[calc(100%+8px)]">
          <ContextMenuListItem>Push to GitHub</ContextMenuListItem>
          <ContextMenuListItem>Download as .zip</ContextMenuListItem>
        </ContextMenu>
      )}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <img src={avatar} alt="" className="w-4 h-4 rounded-full" />
          <a
            href={`https://github.com/${repoName}`}
            target="_blank"
            rel="noreferrer noopener"
          >
            <span className="text-sm leading-6 font-semibold">{repoName}</span>
          </a>
          <ExternalLinkIcon width={16} height={16} />
        </div>
        <div className="text-xs text-[#A3A3A3]">
          <span>{lastCommit.id}</span> <span>&middot;</span>{" "}
          <span>{lastCommit.date}</span>
        </div>
      </div>
      <button
        type="button"
        onClick={toggleMenuVisibility}
        aria-label="Open project menu"
      >
        <EllipsisH width={36} height={36} />
      </button>
    </div>
  );
}

interface ProjectMenuCardProps {
  githubData: {
    avatar: string;
    repoName: string;
    lastCommit: { id: string; date: string };
  } | null;
}

export function ProjectMenuCard({ githubData }: ProjectMenuCardProps) {
  if (githubData) {
    return (
      <DetailedProjectMenuCard
        avatar={githubData.avatar}
        repoName={githubData.repoName}
        lastCommit={githubData.lastCommit}
      />
    );
  }

  return <EmptyProjectMenuCard />;
}
