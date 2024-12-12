import { useTranslation } from "react-i18next";
import LoadingSpinnerOuter from "#/icons/loading-outer.svg?react";
import { cn } from "#/utils/utils";
import ModalBody from "./ModalBody";
import { I18nKey } from "#/i18n/declaration";

interface LoadingSpinnerProps {
  size: "small" | "large";
}

export function LoadingSpinner({ size }: LoadingSpinnerProps) {
  const sizeStyle =
    size === "small" ? "w-[25px] h-[25px]" : "w-[50px] h-[50px]";

  return (
    <div data-testid="loading-spinner" className={cn("relative", sizeStyle)}>
      <div
        className={cn(
          "rounded-full border-4 border-[#525252] absolute",
          sizeStyle,
        )}
      />
      <LoadingSpinnerOuter className={cn("absolute animate-spin", sizeStyle)} />
    </div>
  );
}

interface LoadingProjectModalProps {
  message?: string;
}

function LoadingProjectModal({ message }: LoadingProjectModalProps) {
  const { t } = useTranslation();

  return (
    <ModalBody>
      <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
        {message || t(I18nKey.LOADING_PROJECT$LOADING)}
      </span>
      <LoadingSpinner size="large" />
    </ModalBody>
  );
}

export default LoadingProjectModal;
