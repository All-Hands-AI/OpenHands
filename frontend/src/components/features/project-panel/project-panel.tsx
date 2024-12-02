import { cn } from "#/utils/utils";

export function ProjectPanel() {
  return (
    <div
      className={cn(
        "w-[350px] h-full border border-neutral-700 bg-neutral-900 rounded-xl z-20",
        "absolute left-[calc(100%+12px)]", // 12px padding (sidebar parent)
      )}
    >
      <div className="h-[100px] w-full bg-red-500" />
    </div>
  );
}
