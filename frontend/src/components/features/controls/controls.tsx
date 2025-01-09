import { useParams } from "react-router";
import React from "react";
import posthog from "posthog-js";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { ConversationCard } from "../conversation-panel/conversation-card";
import { DownloadModal } from "#/components/shared/download-modal";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  const params = useParams();
  const { data: conversation } = useUserConversation(
    params.conversationId ?? null,
  );

  const [downloading, setDownloading] = React.useState(false);

  const handleDownloadWorkspace = () => {
    posthog.capture("download_workspace_button_clicked");
    setDownloading(true);
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>

      <ConversationCard
        variant="compact"
        onDownloadWorkspace={handleDownloadWorkspace}
        title={conversation?.title ?? ""}
        lastUpdatedAt={conversation?.created_at ?? ""}
        selectedRepository={conversation?.selected_repository ?? null}
        status={conversation?.status}
      />

      <DownloadModal
        initialPath=""
        onClose={() => setDownloading(false)}
        isOpen={downloading}
      />
    </div>
  );
}
