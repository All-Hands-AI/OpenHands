import React from "react";
import posthog from "posthog-js";
import EllipsisH from "#/icons/ellipsis-h.svg?react";
import { createChatMessage } from "#/services/chat-service";
import { ProjectMenuCardContextMenu } from "./project.menu-card-context-menu";
import { ProjectMenuDetailsPlaceholder } from "./project-menu-details-placeholder";
import { ProjectMenuDetails } from "./project-menu-details";
import { useWsClient } from "#/context/ws-client-provider";
import { ConnectToGitHubModal } from "#/components/shared/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { DownloadModal } from "#/components/shared/download-modal";

interface ProjectMenuCardProps {
  isConnectedToGitHub: boolean;
  githubData: {
    avatar: string | null;
    repoName: string;
    lastCommit: GitHubCommit;
  } | null;
}

export function ProjectMenuCard({
  isConnectedToGitHub,
  githubData,
}: ProjectMenuCardProps) {
  const { send } = useWsClient();

  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);
  const [downloading, setDownloading] = React.useState(false);

  const toggleMenuVisibility = () => {
    setContextMenuIsOpen((prev) => !prev);
  };

  const handlePushToGitHub = () => {
    posthog.capture("push_to_github_button_clicked");
    const rawEvent = {
      content: `
Please push the changes to GitHub and open a pull request.
`,
      imageUrls: [],
      timestamp: new Date().toISOString(),
      pending: false,
    };
    const event = createChatMessage(
      rawEvent.content,
      rawEvent.imageUrls,
      rawEvent.timestamp,
    );

    send(event); // send to socket
    setContextMenuIsOpen(false);
  };

  const handleDownloadWorkspace = () => {
    posthog.capture("download_workspace_button_clicked");
    setDownloading(true);
  };

  const handleDownloadClose = () => {
    setDownloading(false);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {!downloading && contextMenuIsOpen && (
        <ProjectMenuCardContextMenu
          isConnectedToGitHub={isConnectedToGitHub}
          onConnectToGitHub={() => setConnectToGitHubModalOpen(true)}
          onPushToGitHub={handlePushToGitHub}
          onDownloadWorkspace={handleDownloadWorkspace}
          onClose={() => setContextMenuIsOpen(false)}
        />
      )}
      {githubData && (
        <ProjectMenuDetails
          repoName={githubData.repoName}
          avatar={githubData.avatar}
          lastCommit={githubData.lastCommit}
        />
      )}
      {!githubData && (
        <ProjectMenuDetailsPlaceholder
          isConnectedToGitHub={isConnectedToGitHub}
          onConnectToGitHub={() => setConnectToGitHubModalOpen(true)}
        />
      )}
      <DownloadModal
        initialPath=""
        onClose={handleDownloadClose}
        isOpen={downloading}
      />
      {!downloading && (
        <button
          type="button"
          onClick={toggleMenuVisibility}
          aria-label="Open project menu"
        >
          <EllipsisH width={36} height={36} />
        </button>
      )}
      {connectToGitHubModalOpen && (
        <ModalBackdrop onClose={() => setConnectToGitHubModalOpen(false)}>
          <ConnectToGitHubModal
            onClose={() => setConnectToGitHubModalOpen(false)}
          />
        </ModalBackdrop>
      )}
    </div>
  );
}
