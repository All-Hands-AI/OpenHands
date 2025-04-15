import { cn } from "#/utils/utils"

interface BrandButtonProps {
  testId?: string
  variant: "primary" | "secondary"
  type: React.ButtonHTMLAttributes<HTMLButtonElement>["type"]
  isDisabled?: boolean
  className?: string
  onClick?: () => void
  startContent?: React.ReactNode
}

export function BrandButton({
  testId,
  children,
  variant,
  type,
  isDisabled,
  className,
  onClick,
  startContent,
}: React.PropsWithChildren<BrandButtonProps>) {
  return (
    <button
      data-testid={testId}
      disabled={isDisabled}
      // The type is alreadt passed as a prop to the button component
      // eslint-disable-next-line react/button-has-type
      type={type}
      onClick={onClick}
      className={cn(
        "w-fit rounded-lg p-2 text-[14px] font-semibold disabled:cursor-not-allowed disabled:opacity-30",
        variant === "primary" && "bg-primary text-white",
        variant === "secondary" && "border border-primary text-primary",
        startContent && "flex items-center justify-center gap-2",
        className,
      )}
    >
      {startContent}
      {children}
    </button>
  )
}
