import { cn } from "#/utils/utils";

const VALID_WIDTHS = ["w-1/4", "w-1/2", "w-3/4"];

const getRandomWidth = () =>
  VALID_WIDTHS[Math.floor(Math.random() * VALID_WIDTHS.length)];

const getRandomNumber = (from = 3, to = 5) =>
  Math.floor(Math.random() * (to - from + 1)) + from;

function TaskCardSkeleton() {
  return (
    <li className="py-3 border-b border-[#717888] flex items-center pr-6">
      <div className="h-5 w-8 skeleton" />

      <div className="w-full pl-8">
        <div className="h-5 w-24 skeleton mb-2" />
        <div className={cn("h-5 skeleton", getRandomWidth())} />
      </div>

      <div className="h-5 w-16 skeleton" />
    </li>
  );
}

interface TaskGroupSkeletonProps {
  items?: number;
}

function TaskGroupSkeleton({ items = 3 }: TaskGroupSkeletonProps) {
  return (
    <div data-testid="task-group-skeleton">
      <div className="py-3 border-b border-[#717888]">
        <div className="h-6 w-40 skeleton" />
      </div>

      <ul>
        {Array.from({ length: items }).map((_, index) => (
          <TaskCardSkeleton key={index} />
        ))}
      </ul>
    </div>
  );
}

export function TaskSuggestionsSkeleton() {
  return Array.from({ length: getRandomNumber(2, 3) }).map((_, index) => (
    <TaskGroupSkeleton key={index} items={getRandomNumber(3, 5)} />
  ));
}
