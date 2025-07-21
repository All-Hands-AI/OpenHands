import { useEffect, useRef, type ReactNode } from "react";
import { cn } from "../../shared/utils/cn";
export type InteractiveChipType = "elevated" | "filled";

type ButtonStyle = {
  button: string;
  icon: string;
  text: string;
};

export const buttonStyles: Record<InteractiveChipType, ButtonStyle> = {
  elevated: {
    button: cn([
      "ring-1 ring-solid ring-light-neutral-400 rounded-xl bg-light-neutral-950 transition-scale duration-200",
      // hover modifier
      "enabled:hover:bg-light-neutral-800 enabled:hover:ring-light-neutral-15",
      // focus modifier
      "enabled:focus:bg-light-neutral-800 enabled:focus:ring-light-neutral-15",
      // active modifier
      "enabled:active:ring-primary-500 enabled:active:scale-90 enabled:active:bg-light-neutral-900",
      // disabled modifier
      "disabled:opacity-40 disabled:bg-light-neutral-900 disabled:ring-0 disabled:font-medium",
    ]),
    icon: cn([
      "text-light-neutral-400",
      // hover modifier
      "group-enabled:group-hover:font-semibold group-enabled:group-hover:text-light-neutral-15",
      // focus modifier
      "group-enabled:group-focus:font-semibold group-enabled:group-focus:text-light-neutral-15",
      // active modifier
      "group-enabled:group-active:text-primary-500",
    ]),
    text: cn([
      "text-light-neutral-400",
      // hover modifier
      "group-enabled:group-hover:font-semibold group-enabled:group-hover:text-light-neutral-15",
      // focus modifier
      "group-enabled:group-focus:font-semibold group-enabled:group-focus:text-light-neutral-15",
      // active modifier
      "group-enabled:group-active:text-primary-500",
    ]),
  },
  filled: {
    button: cn([
      "rounded-xl bg-light-neutral-600 transition-scale duration-200",
      // hover modifier
      "enabled:hover:bg-light-neutral-300",
      // focus modifier
      "enabled:focus:bg-light-neutral-300",
      // active modifier
      "enabled:active:scale-90 enabled:active:bg-primary-100",
      // disabled modifier
      "disabled:opacity-40 disabled:bg-light-neutral-400 disabled:font-medium",
    ]),
    icon: cn([
      "text-light-neutral-985",
      // hover modifier
      "group-enabled:group-hover:font-semibold",
      // focus modifier
      "group-enabled:group-focus:font-semibold",
      // active modifier
      "group-enabled:group-active:text-light-neutral-970",
    ]),
    text: cn([
      "text-light-neutral-985",
      // hover modifier
      "group-enabled:group-hover:font-semibold",
      // focus modifier
      "group-enabled:group-focus:font-semibold",
      // active modifier
      "group-enabled:group-active:text-light-neutral-970",
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
