import { FaExternalLinkAlt } from "react-icons/fa";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useConversationId } from "#/hooks/use-conversation-id";
import JupyterIcon from "#/icons/jupyter.svg?react";
import OpenHands from "#/api/open-hands";
import TerminalIcon from "#/icons/terminal.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ServerIcon from "#/icons/server.svg?react";
import GitChanges from "#/icons/git_changes.svg?react";
import VSCodeIcon from "#/icons/vscode.svg?react";
import { cn } from "#/utils/utils";
import { useConversationTabs } from "./use-conversation-tabs";
import { ConversationTabNav } from "./conversation-tab-nav";

export function ConversationTabs() {
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const [{ selectedTab, terminalOpen }, { onTabChange, onTerminalChange }] =
    useConversationTabs();

  const { conversationId } = useConversationId();

  const tabs = [
    {
      isActive: selectedTab === "editor",
      icon: GitChanges,
      onClick: () => onTabChange("editor"),
    },
    {
      isActive: selectedTab === "vscode",
      icon: VSCodeIcon,
      onClick: () => onTabChange("vscode"),
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
                  const transformedUrl = transformVSCodeUrl(data.vscode_url);
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
      isActive: terminalOpen,
      icon: TerminalIcon,
      onClick: () => onTerminalChange((prev) => !prev),
    },
    {
      isActive: selectedTab === "jupyter",
      icon: JupyterIcon,
      onClick: () => onTabChange("jupyter"),
    },
    {
      isActive: selectedTab === "served",
      icon: ServerIcon,
      onClick: () => onTabChange("served"),
    },
    {
      isActive: selectedTab === "browser",
      icon: GlobeIcon,
      onClick: () => onTabChange("browser"),
    },
  ];

  return (
    <div
      className={cn(
        "relative w-full",
        "flex flex-row justify-end items-center gap-4.5",
      )}
    >
      {tabs.map(({ icon, rightContent, onClick, isActive }, index) => (
        <ConversationTabNav
          key={index}
          icon={icon}
          onClick={onClick}
          isActive={isActive}
          rightContent={rightContent}
        />
      ))}
    </div>
  );
}
