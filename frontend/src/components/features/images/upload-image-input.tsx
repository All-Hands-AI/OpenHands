import Clip from "#/icons/clip.svg?react";

interface UploadImageInputProps {
  onUpload: (files: File[]) => void;
  label?: React.ReactNode;
}

export function UploadImageInput({ onUpload, label }: UploadImageInputProps) {
  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) onUpload(Array.from(event.target.files));
  };

  return (
    <label className="cursor-pointer py-[10px]">
      {label || <Clip data-testid="default-label" width={24} height={24} />}
      <input
        data-testid="upload-image-input"
        type="file"
        accept="image/*"
        multiple
        hidden
        onChange={handleUpload}
      />
    </label>
  );
}
