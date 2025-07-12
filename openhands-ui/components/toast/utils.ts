import type { IconProps } from "../icon/Icon";

type ToastType = "error" | "success" | "info" | "warning";

export const toastStyles: Record<
  ToastType,
  { icon: IconProps["icon"]; iconColor: string }
> = {
  error: {
    icon: "ExclamationOctagonFill",
    iconColor: "text-red-400",
  },
  success: {
    icon: "CheckCircleFill",
    iconColor: "text-green-500",
  },
  info: {
    icon: "PatchQuestionFill",
    iconColor: "text-aqua-500",
  },
  warning: {
    icon: "ExclamationTriangleFill",
    iconColor: "text-primary-500",
  },
};
