import React from "react";

interface HiddenFileInputProps {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function HiddenFileInput({
  fileInputRef,
  onChange,
}: HiddenFileInputProps) {
  return (
    <input
      type="file"
      ref={fileInputRef}
      multiple
      accept="*/*"
      style={{ display: "none" }}
      onChange={onChange}
      data-testid="upload-image-input"
    />
  );
}
