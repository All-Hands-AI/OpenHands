export function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1.5 rounded-full border border-neutral-1000 bg-white px-3 py-1.5 dark:bg-tertiary">
      <span
        className="h-1.5 w-1.5 translate-y-[-2px] animate-[bounce_0.5s_infinite] rounded-full bg-gray-400"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="h-1.5 w-1.5 translate-y-[-2px] animate-[bounce_0.5s_infinite] rounded-full bg-gray-400"
        style={{ animationDelay: "75ms" }}
      />
      <span
        className="h-1.5 w-1.5 translate-y-[-2px] animate-[bounce_0.5s_infinite] rounded-full bg-gray-400"
        style={{ animationDelay: "150ms" }}
      />
    </div>
  );
}
