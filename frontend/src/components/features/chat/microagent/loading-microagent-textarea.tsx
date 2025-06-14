import { cn } from "#/utils/utils";

export function LoadingMicroagentTextarea() {
  return (
    <textarea
      required
      disabled
      defaultValue=""
      placeholder="Loading prompt..."
      rows={6}
      className={cn(
        "bg-tertiary border border-[#717888] w-full rounded p-2 placeholder:italic placeholder:text-tertiary-alt resize-none",
        "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
      )}
    />
  );
}
