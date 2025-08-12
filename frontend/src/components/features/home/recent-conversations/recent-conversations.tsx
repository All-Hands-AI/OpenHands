import { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { RecentConversationsSkeleton } from "./recent-conversations-skeleton";
import { RecentConversation } from "./recent-conversation";
import { Conversation } from "#/api/open-hands.types";
import { usePaginatedConversations } from "#/hooks/query/use-paginated-conversations";
import { useInfiniteScroll } from "#/hooks/use-infinite-scroll";

export function RecentConversations() {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    data: conversationsList,
    isFetching,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = usePaginatedConversations();

  // Set up infinite scroll
  const scrollContainerRef = useInfiniteScroll({
    hasNextPage: !!hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    threshold: 200, // Load more when 200px from bottom
  });

  const conversations =
    conversationsList?.pages.flatMap((page) => page.results) ?? [];

  // Get the conversations to display based on expanded state
  let displayedConversations: Conversation[] = [];
  if (conversations && conversations.length > 0) {
    if (isExpanded) {
      displayedConversations = conversations.slice(0, 10);
    } else {
      displayedConversations = conversations.slice(0, 3);
    }
  }

  // Check if there are more conversations to show
  const hasMoreConversations = conversations && conversations.length > 3;

  const handleToggle = () => {
    setIsExpanded((prev) => !prev);
  };

  return (
    <section
      data-testid="recent-conversations"
      className="flex flex-col w-full"
    >
      <div className="flex items-center gap-2">
        <h3 className="text-xs leading-4 text-white font-bold py-[14px] pl-4">
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

      {!isFetching && displayedConversations?.length === 0 && (
        <span className="text-sm leading-[16px] text-white font-medium">
          {t(I18nKey.HOME$NO_RECENT_CONVERSATIONS)}
        </span>
      )}

      {!isFetching &&
        displayedConversations &&
        displayedConversations.length > 0 && (
          <div className="flex flex-col">
            <div className="transition-all duration-300 ease-in-out max-h-[420px] overflow-y-auto custom-scrollbar">
              <div ref={scrollContainerRef} className="flex flex-col">
                {displayedConversations.map((conversation) => (
                  <RecentConversation
                    key={conversation.conversation_id}
                    conversation={conversation}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

      {!isFetching && hasMoreConversations && (
        <div className="flex justify-start mt-6 mb-8 ml-4">
          <button
            type="button"
            onClick={handleToggle}
            className="text-xs leading-4 text-[#FAFAFA] font-normal cursor-pointer hover:underline"
          >
            {isExpanded
              ? t(I18nKey.COMMON$VIEW_LESS)
              : t(I18nKey.COMMON$VIEW_MORE)}
          </button>
        </div>
      )}
    </section>
  );
}
