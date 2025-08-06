import { FaExternalLinkAlt } from "react-icons/fa";
import { useSelector } from "react-redux";
import { Container } from "#/components/layout/container";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { TabContent } from "#/components/layout/tab-content";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useConversationId } from "#/hooks/use-conversation-id";
import JupyterIcon from "#/icons/jupyter.svg?react";
import OpenHands from "#/api/open-hands";
import TerminalIcon from "#/icons/terminal.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ServerIcon from "#/icons/server.svg?react";
import GitChanges from "#/icons/git_changes.svg?react";
import VSCodeIcon from "#/icons/vscode.svg?react";

export function ConversationTabs() {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { conversationId } = useConversationId();

  const basePath = `/conversations/${conversationId}`;

  return (
    <Container
      className="h-full w-full"
      labels={[
        {
          to: "",
          icon: GitChanges,
        },
        {
          to: "vscode",
          icon: VSCodeIcon,
          rightContent: !RUNTIME_INACTIVE_STATES.includes(curAgentState) ? (
            <FaExternalLinkAlt
              className="w-3.5 h-3.5 text-inherit"
              onClick={async (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (conversationId) {
                  try {
                    const data = await OpenHands.getVSCodeUrl(conversationId);
                    if (data.vscode_url) {
                      const transformedUrl = transformVSCodeUrl(
                        data.vscode_url,
                      );
                      if (transformedUrl) {
                        window.open(transformedUrl, "_blank");
                      }
                    }
                  } catch (err) {
                    // Silently handle the error
                  }
                }
              }}
            />
          ) : null,
          // },
        },

        {
          to: "terminal",
          icon: TerminalIcon,
        },
        { to: "jupyter", icon: JupyterIcon },
        {
          to: "served",
          icon: ServerIcon,
        },
        {
          to: "browser",
          icon: GlobeIcon,
        },
      ]}
    >
      {/* Use both Outlet and TabContent */}
      <div className="h-full w-full">
        <TabContent conversationPath={basePath} />
      </div>
    </Container>
  );
}
