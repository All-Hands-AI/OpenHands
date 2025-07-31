import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { RecentConversationsSkeleton } from "./recent-conversations-skeleton";
import { RecentConversation } from "./recent-conversation";

export function RecentConversations() {
  const { t } = useTranslation();

  const { data: conversations, isFetching, error } = useUserConversations();

  // Get the top 3 most recent conversations
  const topThreeConversations =
    conversations && conversations.length > 0 ? conversations.slice(0, 3) : [];

  return (
    <section
      data-testid="recent-conversations"
      className="flex flex-col w-full pr-[16px]"
    >
      <div className="flex items-center gap-2">
        <h3 className="text-xs leading-4 text-white font-bold py-[14px]">
          {t(I18nKey.COMMON$RECENT_CONVERSATIONS)}
        </h3>
      </div>

      {error && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-danger">{error.message}</p>
        </div>
      )}

      <div className="flex flex-col">
        {isFetching && <RecentConversationsSkeleton />}
      </div>

      {!isFetching && topThreeConversations?.length === 0 && (
        <span className="text-sm leading-[16px] text-white font-medium">
          {t(I18nKey.TASKS$NO_TASKS_AVAILABLE)}
        </span>
      )}

      {!isFetching &&
        topThreeConversations &&
        topThreeConversations.length > 0 && (
          <div className="flex flex-col">
            {topThreeConversations.map((conversation) => (
              <RecentConversation
                key={conversation.conversation_id}
                conversation={conversation}
              />
            ))}
          </div>
        )}
    </section>
  );
}
