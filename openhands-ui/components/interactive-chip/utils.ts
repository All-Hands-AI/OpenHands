import { cn } from "../../shared/utils/cn";

export type InteractiveChipType = "elevated" | "filled";

export const interactiveChipStyles: Record<InteractiveChipType, string> = {
  elevated: cn([
    // base
    "data-[disabled=false]:border-1 border-light-neutral-400 text-light-neutral-400 bg-light-neutral-950 font-normal",
    // hover modifier
    "hover:border-light-neutral-100 hover:data-[disabled=false]:text-light-neutral-100 hover:data-[disabled=false]:font-semibold hover:data-[disabled=false]:bg-light-neutral-800",
    // focus modifier
    "focus:border-light-neutral-100 focus:text-light-neutral-100 focus:font-semibold focus:bg-light-neutral-800",
    // active modifier
    "active:data-[disabled=false]:border-primary-500 active:data-[disabled=false]:text-primary-500",
    // disabled modifier
    "data-[disabled=true]:opacity-50 data-[disabled=true]:bg-light-neutral-900",
  ]),
  filled: cn([
    // base
    "text-grey-985 bg-light-neutral-600 font-normal",
    // hover modifier
    "hover:data-[disabled=false]:font-semibold hover:data-[disabled=false]:bg-light-neutral-300",
    // focus modifier
    "focus:data-[disabled=false]:font-semibold focus:data-[disabled=false]:bg-light-neutral-300",
    // active modifier
    "active:data-[disabled=false]:bg-primary-100",
    // disabled modifier
    "data-[disabled=true]:opacity-40 data-[disabled=true]:bg-light-neutral-400",
  ]),
};
