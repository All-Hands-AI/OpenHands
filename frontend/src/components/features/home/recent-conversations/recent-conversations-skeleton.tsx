function ConversationSkeleton() {
  return (
    <div className="flex flex-col gap-1 py-[14px]">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full skeleton" />
        <div className="w-27 h-3 skeleton !rounded-sm" />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 skeleton !rounded-sm" />
            <div className="w-30.75 max-w-30.75 h-3 skeleton !rounded-sm" />
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 skeleton !rounded-sm" />
            <div className="w-24 max-w-24 h-3 skeleton !rounded-sm" />
          </div>
        </div>
        <div className="w-10 h-3 skeleton !rounded-sm" />
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
      <div className="w-15 h-3 skeleton !rounded-sm" />
    </div>
  );
}

export function RecentConversationsSkeleton() {
  return <RecentConversationSkeleton />;
}
