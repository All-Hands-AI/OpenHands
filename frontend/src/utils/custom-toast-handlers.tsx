import { toasterMessages } from "@openhands/ui";
import { calculateToastDuration } from "./toast-duration";

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
