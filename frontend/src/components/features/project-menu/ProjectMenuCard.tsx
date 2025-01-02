import React from "react";
import posthog from "posthog-js";
import { useTranslation } from "react-i18next";
import EllipsisH from "#/icons/ellipsis-h.svg?react";
import { ProjectMenuCardContextMenu } from "./project.menu-card-context-menu";
import { ProjectMenuDetailsPlaceholder } from "./project-menu-details-placeholder";
import { ProjectMenuDetails } from "./project-menu-details";
import { ConnectToGitHubModal } from "#/components/shared/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { DownloadModal } from "#/components/shared/download-modal";
import { I18nKey } from "#/i18n/declaration";

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
  const { t } = useTranslation();

  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);
  const [downloading, setDownloading] = React.useState(false);

  const toggleMenuVisibility = () => {
    setContextMenuIsOpen((prev) => !prev);
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
          aria-label={t(I18nKey.PROJECT_MENU_CARD$OPEN)}
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
