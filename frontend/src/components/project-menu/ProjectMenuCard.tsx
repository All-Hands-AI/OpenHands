import React from "react";
import { useDispatch } from "react-redux";
import { useRouteLoaderData } from "@remix-run/react";
import EllipsisH from "#/assets/ellipsis-h.svg?react";
import { ModalBackdrop } from "../modals/modal-backdrop";
import { ConnectToGitHubModal } from "../modals/connect-to-github-modal";
import { addUserMessage } from "#/state/chatSlice";
import { useSocket } from "#/context/socket";
import { createChatMessage } from "#/services/chatService";
import { ProjectMenuCardContextMenu } from "./project.menu-card-context-menu";
import { ProjectMenuDetailsPlaceholder } from "./project-menu-details-placeholder";
import { ProjectMenuDetails } from "./project-menu-details";
import { downloadWorkspace } from "#/utils/download-workspace";
import { clientLoader } from "#/root";
import { isGitHubErrorReponse } from "#/api/github";
import { sendTerminalCommand } from "#/services/terminalService";
import { appendInput } from "#/state/commandSlice";

interface ProjectMenuCardProps {
  isConnectedToGitHub: boolean;
  githubData: {
    avatar: string;
    repoName: string;
    lastCommit: GitHubCommit;
  } | null;
}

export function ProjectMenuCard({
  isConnectedToGitHub,
  githubData,
}: ProjectMenuCardProps) {
  const data = useRouteLoaderData<typeof clientLoader>("root");
  // To avoid re-rendering the component when the user object changes, we memoize the user ID.
  const userId = React.useMemo(() => {
    if (data?.user && !isGitHubErrorReponse(data.user)) return data.user.id;
    return null;
  }, [data?.user]);

  const { send } = useSocket();
  const dispatch = useDispatch();

  const [contextMenuIsOpen, setContextMenuIsOpen] = React.useState(false);
  const [connectToGitHubModalOpen, setConnectToGitHubModalOpen] =
    React.useState(false);

  const exportGitHubTokenToTerminal = (gitHubToken: string) => {
    const command = `export GH_TOKEN=${gitHubToken}`;
    const event = sendTerminalCommand(command);

    send(event);
    dispatch(appendInput(command.replace(gitHubToken, "***")));
  };

  React.useEffect(() => {
    // Export if the user valid
    if (userId && data?.ghToken) exportGitHubTokenToTerminal(data.ghToken);
  }, [userId, data?.ghToken]);

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
        <ProjectMenuCardContextMenu
          isConnectedToGitHub={isConnectedToGitHub}
          onConnectToGitHub={() => setConnectToGitHubModalOpen(true)}
          onPushToGitHub={handlePushToGitHub}
          onDownloadWorkspace={downloadWorkspace}
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
        <EllipsisH width={36} height={36} />
      </button>
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
