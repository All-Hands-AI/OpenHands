import { cn } from "#/utils/utils";

interface LoaderProps {
  size?: "small" | "medium" | "large";
  className?: string;
}

export function Loader({ size = "medium", className }: LoaderProps) {
  const sizeClasses = {
    small: "w-3 h-3",
    medium: "w-4 h-4",
    large: "w-5 h-5",
  };

  const dotSize = sizeClasses[size];

  return (
    <div
      data-testid="loader"
      className={cn("flex items-center justify-center", className)}
    >
      <div className={cn("loader rounded-full", dotSize)} />
    </div>
  );
}
