import { cn } from "../../shared/utils/cn";
import { BaseTypography, type BaseTypographyProps } from "./BaseTypography";

type TypographyProps = Omit<BaseTypographyProps, "as">;
type HeadingTypographyProps = Omit<TypographyProps, "fontSize" | "fontWeight">;

export const Typography = {
  H1: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h1"
      fontSize="xxxl"
      fontWeight={400}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  H2: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h2"
      fontSize="xxl"
      fontWeight={300}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  H3: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h3"
      fontSize="xl"
      fontWeight={600}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  H4: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h4"
      fontSize="xl"
      fontWeight={400}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  H5: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h5"
      fontSize="l"
      fontWeight={400}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  H6: ({ children, className, ...props }: HeadingTypographyProps) => (
    <BaseTypography
      as="h6"
      fontSize="l"
      fontWeight={300}
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  Text: ({ children, className, ...props }: TypographyProps) => (
    <BaseTypography
      as="span"
      className={cn("leading-[120%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
  Code: ({ children, className, ...props }: TypographyProps) => (
    <BaseTypography
      as="span"
      className={cn("tg-family-ibm-plex leading-[140%]", className)}
      {...props}
    >
      {children}
    </BaseTypography>
  ),
};
