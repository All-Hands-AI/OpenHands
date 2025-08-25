import { CSSProperties } from "react";
import { ToastOptions } from "react-hot-toast";
import { toasterMessages } from "@openhands/ui";
import { calculateToastDuration } from "./toast-duration";

const TOAST_STYLE: CSSProperties = {
  background: "#454545",
  border: "1px solid #717888",
  color: "#fff",
  borderRadius: "4px",
};

export const TOAST_OPTIONS: ToastOptions = {
  position: "top-right",
  style: TOAST_STYLE,
};

export const displayErrorToast = (message: string) => {
  const duration = calculateToastDuration(message, 5_000);
  toasterMessages.error(message, { duration, position: "top-right" });
};

export const displaySuccessToast = (message: string) => {
  const duration = calculateToastDuration(message, 5_000);
  toasterMessages.success(message, { duration, position: "top-right" });
};

export const displayWarningToast = (message: string) => {
  const duration = calculateToastDuration(message, 4_000);
  toasterMessages.warning(message, { duration, position: "top-right" });
};
export const displayInfoToast = (message: string) => {
  const duration = calculateToastDuration(message, 4_000);
  toasterMessages.info(message, { duration, position: "top-right" });
};
