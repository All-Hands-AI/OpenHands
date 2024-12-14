import React from "react";
import toast from "react-hot-toast";
import posthog from "posthog-js";
import EllipsisH from "#/icons/ellipsis-h.svg?react";
import { createChatMessage } from "#/services/chat-service";
import { ProjectMenuCardContextMenu } from "./project.menu-card-context-menu";
import { ProjectMenuDetailsPlaceholder } from "./project-menu-details-placeholder";
import { ProjectMenuDetails } from "./project-menu-details";
import { downloadWorkspace } from "#/utils/download-workspace";
import { useWsClient } from "#/context/ws-client-provider";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ConnectToGitHubModal } from "#/components/shared/modals/connect-to-github-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { InstructionsPanel } from "../instructions/instructions-panel";
import { MicroagentsPanel } from "../microagents/microagents-panel";
import { CreateInstructionsModal } from "../../shared/modals/instructions/create-instructions-modal";

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
  const [working, setWorking] = React.useState(false);
  const [createInstructionsModalOpen, setCreateInstructionsModalOpen] = React.useState(false);
  const [hasInstructions, setHasInstructions] = React.useState(false);
  const [hasMicroagents, setHasMicroagents] = React.useState(false);

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
    try {
      setWorking(true);
      downloadWorkspace().then(
        () => setWorking(false),
        () => setWorking(false),
      );
    } catch (error) {
      toast.error("Failed to download workspace");
    }
  };

  const handleAddInstructions = () => {
    posthog.capture("add_instructions_button_clicked");
    setCreateInstructionsModalOpen(true);
  };

  const handleAddTemporaryMicroagent = () => {
    posthog.capture("add_temporary_microagent_button_clicked");
    // TODO: Implement temporary microagent creation
  };

  const handleAddPermanentMicroagent = () => {
    posthog.capture("add_permanent_microagent_button_clicked");
    // TODO: Implement permanent microagent creation
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
        {!working && contextMenuIsOpen && (
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
        <button
          type="button"
          onClick={toggleMenuVisibility}
          aria-label="Open project menu"
        >
          {working ? (
            <LoadingSpinner size="small" />
          ) : (
            <EllipsisH width={36} height={36} />
          )}
        </button>
        {connectToGitHubModalOpen && (
          <ModalBackdrop onClose={() => setConnectToGitHubModalOpen(false)}>
            <ConnectToGitHubModal
              onClose={() => setConnectToGitHubModalOpen(false)}
            />
          </ModalBackdrop>
        )}
      </div>

      {githubData && (
        <>
          <InstructionsPanel
            repoName={githubData.repoName}
            hasInstructions={hasInstructions}
            tutorialUrl={`https://github.com/${githubData.repoName}/blob/main/.openhands_instructions`}
            onAddInstructions={handleAddInstructions}
          />
          <MicroagentsPanel
            repoName={githubData.repoName}
            hasMicroagents={hasMicroagents}
            onAddTemporary={handleAddTemporaryMicroagent}
            onAddPermanent={handleAddPermanentMicroagent}
          />
        </>
      )}

      {createInstructionsModalOpen && (
        <CreateInstructionsModal
          repoName={githubData?.repoName || ""}
          onClose={() => setCreateInstructionsModalOpen(false)}
          onCreateInstructions={() => {
            // TODO: Implement instructions creation
            setCreateInstructionsModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
