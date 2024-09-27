import React from "react";
import { useDispatch } from "react-redux";
import EllipsisH from "#/assets/ellipsis-h.svg?react";
import CloudConnection from "#/assets/cloud-connection.svg?react";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ModalBackdrop } from "../modals/modal-backdrop";
import { ConnectToGitHubModal } from "../modals/connect-to-github-modal";
import { cn } from "#/utils/utils";
import ExternalLinkIcon from "#/assets/external-link.svg?react";
import { retrieveWorkspaceZipBlob } from "#/api/open-hands";
import { addUserMessage } from "#/state/chatSlice";
import { useSocket } from "#/context/socket";
import { createChatMessage } from "#/services/chatService";
import { formatTimeDelta } from "#/utils/format-time-delta";

const downloadWorkspace = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("No token found");
    }

    const blob = await retrieveWorkspaceZipBlob(token);

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "workspace.zip");
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  } catch (e) {
    console.error("Failed to download workspace as .zip", e);
  }
};

// TODO: Merge the two component variants into one

interface EmptyProjectMenuCardProps {
  isConnectedToGitHub: boolean;
}

function EmptyProjectMenuCard({
  isConnectedToGitHub,
}: EmptyProjectMenuCardProps) {
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
          {!isConnectedToGitHub && (
            <ContextMenuListItem
              onClick={() => setConnectToGitHubModalOpen(true)}
            >
              Connect to GitHub
            </ContextMenuListItem>
          )}
          <ContextMenuListItem onClick={downloadWorkspace}>
            Download as .zip
          </ContextMenuListItem>
        </ContextMenu>
      )}
      <div className="flex flex-col">
        <span className="text-sm leading-6 font-semibold">New Project</span>
        <button
          type="button"
          onClick={() => setConnectToGitHubModalOpen(true)}
          disabled={isConnectedToGitHub}
        >
          <span
            className={cn(
              "text-xs leading-4 text-[#A3A3A3] flex items-center gap-2",
              "hover:underline hover:underline-offset-2",
            )}
          >
            {!isConnectedToGitHub ? "Connect to GitHub" : "Connected"}
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
  lastCommit: GitHubCommit;
}

function DetailedProjectMenuCard({
  avatar,
  repoName,
  lastCommit,
}: DetailedProjectMenuCardProps) {
  const { send } = useSocket();
  const dispatch = useDispatch();
  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);

  const toggleMenuVisibility = () => {
    setContextMenuIsOpen((prev) => !prev);
  };

  const handlePushToGitHub = () => {
    const rawEvent = {
      content: "Please commit and push these changes to the repository.",
      imageUrls: [],
      timestamp: new Date().toISOString(),
    };
    const event = createChatMessage(
      rawEvent.content,
      rawEvent.imageUrls,
      rawEvent.timestamp,
    );

    send(event); // send to socket
    dispatch(addUserMessage(rawEvent)); // display in chat interface
    setContextMenuIsOpen(false);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {contextMenuIsOpen && (
        <ContextMenu className="absolute right-0 bottom-[calc(100%+8px)]">
          <ContextMenuListItem onClick={handlePushToGitHub}>
            Push to GitHub
          </ContextMenuListItem>
          <ContextMenuListItem>Download as .zip</ContextMenuListItem>
        </ContextMenu>
      )}
      <div className="flex flex-col">
        <a
          href={`https://github.com/${repoName}`}
          target="_blank"
          rel="noreferrer noopener"
          className="flex items-center gap-2"
        >
          <img src={avatar} alt="" className="w-4 h-4 rounded-full" />
          <span className="text-sm leading-6 font-semibold">{repoName}</span>
          <ExternalLinkIcon width={16} height={16} />
        </a>
        <a
          href={lastCommit.html_url}
          target="_blank"
          rel="noreferrer noopener"
          className="text-xs text-[#A3A3A3] hover:underline hover:underline-offset-2"
        >
          <span>{lastCommit.sha.slice(-7)}</span> <span>&middot;</span>{" "}
          <span>
            {formatTimeDelta(new Date(lastCommit.commit.author.date))} ago
          </span>
        </a>
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
  token: string | null;
  githubData: {
    avatar: string;
    repoName: string;
    lastCommit: GitHubCommit;
  } | null;
}

export function ProjectMenuCard({ token, githubData }: ProjectMenuCardProps) {
  if (githubData) {
    return (
      <DetailedProjectMenuCard
        avatar={githubData.avatar}
        repoName={githubData.repoName}
        lastCommit={githubData.lastCommit}
      />
    );
  }

  return <EmptyProjectMenuCard isConnectedToGitHub={!!token} />;
}
