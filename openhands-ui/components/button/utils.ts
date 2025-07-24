import { useEffect, useRef, type ReactNode } from "react";
import type { ComponentVariant } from "../../shared/types";
import { cn } from "../../shared/utils/cn";

type ButtonStyle = {
  button: string;
  icon: string;
  text: string;
};

export const buttonStyles: Record<ComponentVariant, ButtonStyle> = {
  primary: {
    button: cn([
      "ring-1 ring-solid ring-primary-500 rounded-full bg-grey-950",
      // hover modifier
      "enabled:hover:bg-grey-900 enabled:hover:ring-[1.5px]",
      // focus modifier
      "enabled:hover:bg-grey-900 enabled:focus-visible:ring-[1.5px]",
      // active modifier
      "enabled:active:ring-1",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-primary-500"]),
    text: cn([
      "text-primary-500",
      // hover modifier
      "group-enabled:group-hover:font-semibold",
      // focus modifier
      "group-enabled:group-focus-visible:font-semibold",
      // active modifier
      "group-enabled:group-active:font-normal",
    ]),
  },
  secondary: {
    button: cn([
      "ring-1 ring-solid ring-light-neutral-300 rounded-full bg-light-neutral-950",
      // hover modifier
      "enabled:hover:bg-light-neutral-900 enabled:hover:ring-[1.5px]",
      // focus modifier
      "enabled:focus-visible:bg-light-neutral-900 enabled:focus-visible:ring-[1.5px]",
      // active modifier
      "enabled:active:ring-1",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-light-neutral-300"]),
    text: cn([
      "text-light-neutral-300",
      // hover modifier
      "group-enabled:group-hover:font-semibold",
      // focus modifier
      "group-enabled:group-focus-visible:font-semibold",
      // active modifier
      "group-enabled:group-active:font-normal",
    ]),
  },
  tertiary: {
    button: cn([
      "rounded-full",
      // hover modifier
      "enabled:hover:bg-grey-900",
      // focus modifier
      "enabled:focus-visible:bg-grey-900",
      // active modifier
      "enabled:active:bg-grey-970",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-primary-500"]),
    text: cn([
      "text-primary-500 underline",
      // hover modifier
      "group-enabled:group-hover:font-semibold",
      // focus modifier
      "group-enabled:group-focus-visible:font-semibold",
      // disabled modifier
      "group-disabled:no-underline",
      // active modifier
      "group-enabled:group-active:font-normal",
    ]),
  },
};

/**
 * Custom hook that calculates and applies a CSS custom property (variable)
 * based on the length of a text node. Useful for adjusting spacing or layout
 * to account for changes in font weight, such as bold text rendering wider.
 */
const BOLD_TEXT_INCREASE = 0.15;
export const useAndApplyBoldTextWidth = (
  textNode: ReactNode,
  varName: string
) => {
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (textRef) {
      const charCount =
        typeof textNode === "string" ? (textNode as string).length : 0;
      const textIncrease = charCount * BOLD_TEXT_INCREASE;
      textRef.current!.style.setProperty(`--${varName}`, `${textIncrease}px`);
    }
  }, [textRef.current]);

  return textRef;
};
