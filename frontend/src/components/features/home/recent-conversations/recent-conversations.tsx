import { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { RecentConversationsSkeleton } from "./recent-conversations-skeleton";
import { RecentConversation } from "./recent-conversation";
import { usePaginatedConversations } from "#/hooks/query/use-paginated-conversations";
import { useInfiniteScroll } from "#/hooks/use-infinite-scroll";
import { cn } from "#/utils/utils";

export function RecentConversations() {
  const { t } = useTranslation();
  const [displayCount, setDisplayCount] = useState(3);

  const {
    data: conversationsList,
    isFetching,
    isFetchingNextPage,
    error,
    hasNextPage,
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

  // Get the conversations to display based on current display count
  const displayedConversations = conversations.slice(0, displayCount);

  const hasConversations = conversations && conversations.length > 0;

  // Check if there are more conversations to show
  const hasMoreConversations =
    conversations && conversations.length > displayCount;

  // Check if we've reached the maximum display limit
  const isAtMaxDisplay = displayCount >= 10;

  // Check if we can show more conversations (not at max and have more available)
  const canShowMore = !isAtMaxDisplay && hasMoreConversations;

  // Check if we should show the "View Less" button (showing all conversations or at max)
  const shouldShowViewLess =
    displayCount > 3 && (!hasMoreConversations || isAtMaxDisplay);

  // Check if this is the initial load (no data yet)
  const isInitialLoading = isFetching && !conversationsList;

  const handleViewMore = () => {
    // Calculate the next display count (increment by 3, but don't exceed 10)
    const nextCount = Math.min(displayCount + 3, 10);
    setDisplayCount(nextCount);
  };

  const handleViewLess = () => {
    // Reset to showing only 3 conversations
    setDisplayCount(3);
  };

  return (
    <section
      data-testid="recent-conversations"
      className="flex flex-col w-full"
    >
      <div
        className={cn(
          "flex items-center gap-2",
          !hasConversations && "mb-[14px]",
        )}
      >
        <h3 className="text-xs leading-4 text-white font-bold py-[14px] pl-4">
          {t(I18nKey.COMMON$RECENT_CONVERSATIONS)}
        </h3>
      </div>

      {error && (
        <div className="flex flex-col items-center justify-center h-full pl-4">
          <p className="text-danger">{error.message}</p>
        </div>
      )}

      <div className="flex flex-col">
        {isInitialLoading && (
          <div className="pl-4">
            <RecentConversationsSkeleton />
          </div>
        )}
      </div>

      {!isInitialLoading && displayedConversations?.length === 0 && (
        <span className="text-xs leading-4 text-white font-medium pl-4">
          {t(I18nKey.HOME$NO_RECENT_CONVERSATIONS)}
        </span>
      )}

      {!isInitialLoading &&
        displayedConversations &&
        displayedConversations.length > 0 && (
          <div className="flex flex-col">
            <div className="transition-all duration-300 ease-in-out overflow-y-auto custom-scrollbar">
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

      {!isInitialLoading && (canShowMore || shouldShowViewLess) && (
        <div className="flex justify-start mt-6 mb-8 ml-4">
          <button
            type="button"
            onClick={shouldShowViewLess ? handleViewLess : handleViewMore}
            className="text-xs leading-4 text-[#FAFAFA] font-normal cursor-pointer hover:underline"
          >
            {shouldShowViewLess
              ? t(I18nKey.COMMON$VIEW_LESS)
              : t(I18nKey.COMMON$VIEW_MORE)}
          </button>
        </div>
      )}
    </section>
  );
}
