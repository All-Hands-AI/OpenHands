import { Skeleton } from "@heroui/react";

interface SkeletonMessageProps {
  type?: "user" | "assistant";
}

export function SkeletonMessage({ type = "assistant" }: SkeletonMessageProps) {
  const isUser = type === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      {isUser && (
        <Skeleton className="h-[80px] w-1/2 rounded-lg bg-neutral-1000" />
      )}
      {!isUser && (
        <div className="flex flex-col gap-2 w-full">
          <Skeleton className="h-[30px] w-[50%] rounded-lg bg-neutral-1000" />
          <Skeleton className="h-[60px] w-[60%] rounded-lg bg-neutral-1000" />
        </div>
      )}
    </div>
  );
}
