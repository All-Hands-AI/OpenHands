import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { Typography } from "@openhands/ui";
import { RootState } from "#/store";
import { useWsClient } from "#/context/ws-client-provider";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { getStatusCode } from "#/utils/status";

export interface AgentStatusProps {
  className?: string;
}

export function AgentStatus({ className = "" }: AgentStatusProps) {
  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const { curStatusMessage } = useSelector((state: RootState) => state.status);
  const { webSocketStatus } = useWsClient();
  const { data: conversation } = useActiveConversation();

  const statusCode = getStatusCode(
    curStatusMessage,
    webSocketStatus,
    conversation?.status || null,
    conversation?.runtime_status || null,
    curAgentState,
  );

  return (
    <div className={`flex items-center ${className}`}>
      <Typography.Text className="text-[11px] text-[#D0D9FA] font-normal leading-5">
        {t(statusCode)}
      </Typography.Text>
    </div>
  );
}

export default AgentStatus;
