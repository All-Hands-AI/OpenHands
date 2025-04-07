import { cn } from "#/utils/utils";

interface BrandButtonProps {
  testId?: string;
  variant: "primary" | "secondary";
  type: React.ButtonHTMLAttributes<HTMLButtonElement>["type"];
  isDisabled?: boolean;
  className?: string;
  onClick?: () => void;
}

export function BrandButton({
  testId,
  children,
  variant,
  type,
  isDisabled,
  className,
  onClick,
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
        "w-fit p-2 rounded disabled:opacity-30 disabled:cursor-not-allowed",
        variant === "primary" && "bg-primary text-[#0D0F11]",
        variant === "secondary" && "border border-primary text-primary",
        className,
      )}
    >
      {children}
    </button>
  );
}
