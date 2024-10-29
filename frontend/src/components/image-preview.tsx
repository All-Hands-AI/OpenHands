import CloseIcon from "#/assets/close.svg?react";
import { cn } from "#/utils/utils";

interface ImagePreviewProps {
  src: string;
  onRemove?: () => void;
  size?: "small" | "large";
}

export function ImagePreview({
  src,
  onRemove,
  size = "small",
}: ImagePreviewProps) {
  return (
    <div data-testid="image-preview" className="relative w-fit shrink-0">
      <img
        role="img"
        src={src}
        alt=""
        className={cn(
          "rounded object-cover",
          size === "small" && "w-[62px] h-[62px]",
          size === "large" && "w-[100px] h-[100px]",
        )}
      />
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className={cn(
            "bg-neutral-400 rounded-full w-3 h-3 flex items-center justify-center",
            "absolute right-[3px] top-[3px]",
          )}
        >
          <CloseIcon width={10} height={10} />
        </button>
      )}
    </div>
  );
}
