import type { PropsWithChildren } from "react";
import {
  fontSizes,
  fontWeights,
  type FontSize,
  type FontWeight,
} from "./utils";
import { cn } from "../../shared/utils/cn";
import type { BaseProps } from "../../shared/types";

type SupportedReactNodes = "h6" | "h5" | "h4" | "h3" | "h2" | "h1" | "span";

export type BaseTypographyProps = React.HTMLAttributes<HTMLElement> & {
  fontSize?: FontSize;
  fontWeight?: FontWeight;
  as: SupportedReactNodes;
} & BaseProps;

export const BaseTypography = ({
  fontSize,
  fontWeight,
  className,
  children,
  as,
  testId,
  ...props
}: PropsWithChildren<BaseTypographyProps>) => {
  const Component = as;

  return (
    <Component
      {...props}
      data-testid={testId}
      className={cn(
        "tg-family-outfit text-white leading-[100%]",
        fontSize ? fontSizes[fontSize] : undefined,
        fontWeight ? fontWeights[fontWeight] : undefined,
        className
      )}
    >
      {children}
    </Component>
  );
};
