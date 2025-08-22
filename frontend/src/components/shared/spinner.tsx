import { cn } from "#/utils/utils";

interface SpinnerProps {
  size?: "small" | "medium" | "large";
  className?: string;
  "data-testid"?: string;
}

const SIZE_CLASSES = {
  small: "w-5 h-5",
  medium: "w-8 h-8",
  large: "w-12 h-12",
};

export function Spinner({
  size = "medium",
  className,
  "data-testid": testId = "spinner",
}: SpinnerProps) {
  return (
    <div
      data-testid={testId}
      className={cn(
        "inline-block animate-spin rounded-full border-4 border-gray-200 border-t-blue-500",
        SIZE_CLASSES[size],
        className,
      )}
      role="status"
      aria-label="Loading"
    />
  );
}
