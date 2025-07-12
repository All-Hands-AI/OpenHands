import { cloneElement, isValidElement, type ReactElement } from "react";
import type { ComponentVariant, HTMLProps } from "../../shared/types";

export const cloneIcon = (
  icon?: ReactElement<HTMLProps<"svg">>,
  props?: HTMLProps<"svg">
) => {
  if (!icon) {
    return null;
  }
  if (!isValidElement(icon)) {
    return null;
  }
  return cloneElement(icon, props ?? {});
};
