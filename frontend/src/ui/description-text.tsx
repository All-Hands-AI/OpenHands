import { ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "#/utils/utils";

const descriptionTextVariants = cva("text-sm font-normal text-white", {
  variants: {
    lineHeight: {
      default: "leading-[22px]",
      tight: "leading-5",
    },
  },
  defaultVariants: {
    lineHeight: "default",
  },
});

interface DescriptionTextProps
  extends VariantProps<typeof descriptionTextVariants> {
  children: ReactNode;
  className?: string;
}

export function DescriptionText({
  children,
  className = "",
  lineHeight,
}: DescriptionTextProps) {
  return (
    <div className={className}>
      <span className={cn(descriptionTextVariants({ lineHeight }), className)}>
        {children}
      </span>
    </div>
  );
}
