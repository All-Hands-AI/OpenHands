import type { PropsWithChildren } from "react";
import {
  fontSizes,
  fontWeights,
  type FontSize,
  type FontWeight,
} from "./utils";
import { cn } from "../../shared/utils/cn";

type SupportedReactNodes = "h6" | "h5" | "h4" | "h3" | "h2" | "h1" | "span";

export type BaseTypographyProps = React.HTMLAttributes<HTMLElement> & {
  fontSize?: FontSize;
  fontWeight?: FontWeight;
  as: SupportedReactNodes;
};

export const BaseTypography = ({
  fontSize,
  fontWeight,
  className,
  children,
  as,
  ...props
}: PropsWithChildren<BaseTypographyProps>) => {
  const Component = as;

  return (
    <Component
      {...props}
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
