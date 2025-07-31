import { cloneElement, isValidElement, type ReactElement } from "react";
import type { BaseProps, HTMLProps } from "../../shared/types";

export const cloneIcon = (
  icon?: ReactElement<HTMLProps<"svg"> & BaseProps>,
  props?: HTMLProps<"svg"> & BaseProps
) => {
  if (!icon) {
    return null;
  }
  if (!isValidElement(icon)) {
    return null;
  }
  return cloneElement(icon, props ?? {});
};
