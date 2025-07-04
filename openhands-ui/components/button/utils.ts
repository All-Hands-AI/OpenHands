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
      "enabled:hover:bg-grey-900 enabled:focus:ring-[1.5px]",
      // active modifier
      "enabled:active:ring-1",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-primary-500"]),
    text: cn(["text-primary-500"]),
  },
  secondary: {
    button: cn([
      "ring-1 ring-solid ring-light-neutral-300 rounded-full bg-light-neutral-950",
      // hover modifier
      "enabled:hover:bg-light-neutral-900 enabled:hover:ring-[1.5px]",
      // focus modifier
      "enabled:focus:bg-light-neutral-900 enabled:focus:ring-[1.5px]",
      // active modifier
      "enabled:active:ring-1",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-light-neutral-300"]),
    text: cn(["text-light-neutral-300"]),
  },
  tertiary: {
    button: cn([
      "rounded-full",
      // hover modifier
      "enabled:hover:bg-grey-900",
      // focus modifier
      "enabled:focus:bg-grey-900",
      // active modifier
      "enabled:active:bg-grey-970",
      // disabled modifier
      "disabled:opacity-50",
    ]),
    icon: cn(["text-primary-500"]),
    text: cn([
      "text-primary-500 underline",
      // disabled modifier
      "group-disabled:no-underline",
    ]),
  },
};
