import { cn } from "#/utils/utils";

interface BrandButtonProps {
  testId?: string;
  name?: string;
  variant: "primary" | "secondary" | "danger" | "glow";
  type: React.ButtonHTMLAttributes<HTMLButtonElement>["type"];
  isDisabled?: boolean;
  className?: string;
  onClick?: () => void;
  startContent?: React.ReactNode;
}

export function BrandButton({
  testId,
  name,
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
      name={name}
      data-testid={testId}
      disabled={isDisabled}
      // The type is alreadt passed as a prop to the button component
      // eslint-disable-next-line react/button-has-type
      type={type}
      onClick={onClick}
      className={cn(
        "w-fit px-3 py-2 text-sm rounded-sm disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-90 cursor-pointer transition-colors transition-shadow duration-150",
        // Primary: brand gold with inner softness and gold glow on focus
        variant === "primary" &&
          "bg-primary text-[#0D0F11] shadow-inner-soft focus:outline-none focus:ring-2 focus:ring-gold",
        // Secondary: outline gold with hover fill
        variant === "secondary" &&
          "border border-primary text-primary hover:bg-primary/10",
        // Danger stays as is
        variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
        // Glow: neon accent with outer glow
        variant === "glow" &&
          "bg-accent/10 text-accent border border-accent/40 shadow-glow-accent hover:bg-accent/20",
        startContent && "flex items-center justify-center gap-2",
        className,
      )}
    >
      {startContent}
      {children}
    </button>
  );
}
