import LoadingSpinnerOuter from "#/assets/loading-outer.svg?react";
import { cn } from "#/utils/utils";
import ModalBody from "./ModalBody";

interface LoadingSpinnerProps {
  size: "small" | "large";
}

export function LoadingSpinner({ size }: LoadingSpinnerProps) {
  const sizeStyle =
    size === "small" ? "w-[25px] h-[25px]" : "w-[50px] h-[50px]";

  return (
    <div className={cn("relative", sizeStyle)}>
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
  return (
    <ModalBody>
      <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
        {message || "Loading..."}
      </span>
      <LoadingSpinner size="large" />
    </ModalBody>
  );
}

export default LoadingProjectModal;
