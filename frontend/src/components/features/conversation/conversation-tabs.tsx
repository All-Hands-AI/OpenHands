import { DiGit } from "react-icons/di";
import { FaServer, FaExternalLinkAlt } from "react-icons/fa";
import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
import { Container } from "#/components/layout/container";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { ServedAppLabel } from "#/components/layout/served-app-label";
import { TabContent } from "#/components/layout/tab-content";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useConversationId } from "#/hooks/use-conversation-id";
import GlobeIcon from "#/icons/globe.svg?react";
import JupyterIcon from "#/icons/jupyter.svg?react";
import OpenHands from "#/api/open-hands";
import TerminalIcon from "#/icons/terminal.svg?react";

export function ConversationTabs() {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { conversationId } = useConversationId();

  const { t } = useTranslation();

  const basePath = `/conversations/${conversationId}`;

  return (
    <Container
      className="h-full w-full"
      labels={[
        {
          label: "Changes",
          to: "",
          icon: <DiGit className="w-6 h-6" />,
        },
        {
          label: (
            <div className="flex items-center gap-1">
              {t(I18nKey.VSCODE$TITLE)}
            </div>
          ),
          to: "vscode",
          icon: <VscCode className="w-5 h-5" />,
          rightContent: !RUNTIME_INACTIVE_STATES.includes(curAgentState) ? (
            <FaExternalLinkAlt
              className="w-3 h-3 text-neutral-400 cursor-pointer"
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
        },
        {
          label: t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL),
          to: "terminal",
          icon: <TerminalIcon />,
        },
        { label: "Jupyter", to: "jupyter", icon: <JupyterIcon /> },
        {
          label: <ServedAppLabel />,
          to: "served",
          icon: <FaServer />,
        },
        {
          label: (
            <div className="flex items-center gap-1">
              {t(I18nKey.BROWSER$TITLE)}
            </div>
          ),
          to: "browser",
          icon: <GlobeIcon />,
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
