import LoadingSpinnerOuter from "#/icons/loading-outer.svg?react"
import { cn } from "#/utils/utils"

interface LoadingSpinnerProps {
  size: "small" | "large"
}

export function LoadingSpinner({ size }: LoadingSpinnerProps) {
  const sizeStyle = size === "small" ? "w-[25px] h-[25px]" : "w-[50px] h-[50px]"

  return (
    <div data-testid="loading-spinner" className={cn("relative", sizeStyle)}>
      <div
        className={cn(
          "absolute rounded-full border-4 border-primary",
          sizeStyle,
        )}
      />
      <LoadingSpinnerOuter className={cn("absolute animate-spin", sizeStyle)} />
    </div>
  )
}
