import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "#/utils/utils";

const typographyVariants = cva("", {
  variants: {
    variant: {
      h1: "text-[32px] text-white font-bold leading-5",
      span: "text-sm font-normal text-white leading-5.5",
    },
  },
  defaultVariants: {
    variant: "h1",
  },
});

interface TypographyProps extends VariantProps<typeof typographyVariants> {
  className?: string;
  testId?: string;
  children: React.ReactNode;
}

export function Typography({
  variant,
  className,
  testId,
  children,
}: TypographyProps) {
  const Tag = variant as keyof React.JSX.IntrinsicElements;

  return (
    <Tag
      data-testid={testId}
      className={cn(typographyVariants({ variant }), className)}
    >
      {children}
    </Tag>
  );
}

// Export individual heading components for convenience
export function H1({
  className,
  testId,
  children,
}: Omit<TypographyProps, "variant">) {
  return (
    <Typography variant="h1" className={className} testId={testId}>
      {children}
    </Typography>
  );
}

export function Text({
  className,
  testId,
  children,
}: Omit<TypographyProps, "variant">) {
  return (
    <Typography variant="span" className={className} testId={testId}>
      {children}
    </Typography>
  );
}

// Attach components to Typography for the expected API
Typography.H1 = H1;
Typography.Text = Text;
