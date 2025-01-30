import { cn } from "@nextui-org/react";

interface BrandButtonProps {
  variant: "primary" | "secondary";
}

export function BrandButton({
  children,
  variant,
}: React.PropsWithChildren<BrandButtonProps>) {
  return (
    <button
      type="button"
      className={cn(
        "w-fit p-2 rounded",
        variant === "primary" && "bg-[#C9B974] text-[#0D0F11]",
        variant === "secondary" && "border border-[#C9B974] text-[#C9B974]",
      )}
    >
      {children}
    </button>
  );
}
