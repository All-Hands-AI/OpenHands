import Clip from "#/assets/clip.svg?react";

interface UploadImageInputProps {
  onUpload: (files: File[]) => void;
}

export function UploadImageInput({ onUpload }: UploadImageInputProps) {
  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) onUpload(Array.from(event.target.files));
  };

  return (
    <label className="cursor-pointer">
      <Clip width={24} height={24} />
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
