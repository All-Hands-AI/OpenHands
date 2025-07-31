import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import CodeBranchIcon from "#/icons/u-code-branch.svg?react";
import { Conversation } from "#/api/open-hands.types";
import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import { Provider } from "#/types/settings";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatusIndicator } from "./conversation-status-indicator";

interface RecentConversationProps {
  conversation: Conversation;
}

export function RecentConversation({ conversation }: RecentConversationProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleConversationClick = () => {
    navigate(`/conversations/${conversation.conversation_id}`);
  };

  return (
    <div
      className="flex flex-col gap-1 py-[14px] cursor-pointer"
      onClick={handleConversationClick}
    >
      <div className="flex items-center gap-2">
        <ConversationStatusIndicator conversationStatus={conversation.status} />
        <span className="text-xs text-white leading-6 font-normal">
          {conversation.title}
        </span>
      </div>
      {conversation.selected_repository && conversation.selected_branch && (
        <div className="flex items-center justify-between text-xs text-[#A3A3A3] leading-4 font-normal">
          <div className="flex items-center gap-2">
            <GitProviderIcon
              gitProvider={conversation.git_provider as Provider}
            />
            <span className="">{conversation.selected_repository}</span>
          </div>
          <div className="flex items-center gap-1">
            <CodeBranchIcon width={12} height={12} color="#A3A3A3" />
            <span className="max-w-[124px] truncate">
              {conversation.selected_branch}
            </span>
          </div>
          <span>
            {formatTimeDelta(
              new Date(conversation.created_at || conversation.last_updated_at),
            )}{" "}
            {t(I18nKey.CONVERSATION$AGO)}
          </span>
        </div>
      )}
    </div>
  );
}
