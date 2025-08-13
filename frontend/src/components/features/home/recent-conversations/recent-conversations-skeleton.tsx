const getRandomNumber = (from = 3, to = 5) =>
  Math.floor(Math.random() * (to - from + 1)) + from;

function ConversationSkeleton() {
  return (
    <div className="flex flex-col gap-1 py-[14px]">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full skeleton" />
        <div className="w-20 h-3 skeleton" />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 skeleton rounded-sm" />
          <div className="w-20 max-w-20 h-3 skeleton" />
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 skeleton rounded-sm" />
          <div className="w-20 max-w-20 h-3 skeleton" />
        </div>
        <div className="w-8 h-3 skeleton" />
      </div>
    </div>
  );
}

interface RecentConversationSkeletonProps {
  items?: number;
}

function RecentConversationSkeleton({
  items = 3,
}: RecentConversationSkeletonProps) {
  return (
    <div data-testid="recent-conversations-skeleton">
      <ul>
        {Array.from({ length: items }).map((_, index) => (
          <ConversationSkeleton key={index} />
        ))}
      </ul>
    </div>
  );
}

export function RecentConversationsSkeleton() {
  return Array.from({ length: getRandomNumber(2, 3) }).map((_, index) => (
    <RecentConversationSkeleton key={index} items={getRandomNumber(3, 5)} />
  ));
}
