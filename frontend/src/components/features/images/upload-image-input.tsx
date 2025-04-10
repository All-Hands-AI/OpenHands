import Clip from "#/icons/clip.svg?react";
import { twMerge } from "tailwind-merge";

interface UploadImageInputProps {
  onUpload: (files: File[]) => void;
  label?: React.ReactNode;
  isDisabled?: boolean;
}

export function UploadImageInput({
  onUpload,
  label,
  isDisabled = false,
}: UploadImageInputProps) {
  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) onUpload(Array.from(event.target.files));
  };

  return (
    <label
      className={twMerge(
        "cursor-pointer py-[10px]",
        isDisabled && "!cursor-not-allowed",
      )}
    >
      {label || (
        <Clip
          data-testid="default-label"
          width={24}
          height={24}
          className={twMerge(" rotate-45", isDisabled && "cursor-not-allowed")}
        />
      )}
      <input
        disabled={isDisabled}
        data-testid="upload-image-input"
        type="file"
        accept="image/*"
        multiple
        hidden
        className="disabled:cursor-not-allowed"
        onChange={handleUpload}
      />
    </label>
  );
}
