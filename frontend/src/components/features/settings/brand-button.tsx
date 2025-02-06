import { cn } from "@nextui-org/react";

interface BrandButtonProps {
  variant: "primary" | "secondary";
  type: React.ButtonHTMLAttributes<HTMLButtonElement>["type"];
  className?: string;
  onClick?: () => void;
}

export function BrandButton({
  children,
  variant,
  type,
  className,
  onClick,
}: React.PropsWithChildren<BrandButtonProps>) {
  return (
    <button
      // The type is alreadt passed as a prop to the button component
      // eslint-disable-next-line react/button-has-type
      type={type}
      onClick={onClick}
      className={cn(
        "w-fit p-2 rounded",
        variant === "primary" && "bg-[#C9B974] text-[#0D0F11]",
        variant === "secondary" && "border border-[#C9B974] text-[#C9B974]",
        className,
      )}
    >
      {children}
    </button>
  );
}
