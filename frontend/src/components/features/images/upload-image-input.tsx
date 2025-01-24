import { useTranslation } from "react-i18next";
import Clip from "#/icons/clip.svg?react";
import { getValidImageFiles } from "#/utils/validate-image-type";
import { toast } from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";

interface UploadImageInputProps {
  onUpload: (files: File[]) => void;
  label?: React.ReactNode;
}

export function UploadImageInput({ onUpload, label }: UploadImageInputProps) {
  const { t } = useTranslation();

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;

    const files = Array.from(event.target.files);
    const { validFiles, invalidFiles } = getValidImageFiles(files);

    if (invalidFiles.length > 0) {
      toast.error(
        t(I18nKey.UPLOAD$UNSUPPORTED_IMAGE_TYPE, {
          count: invalidFiles.length,
          files: invalidFiles.map((f) => f.name).join(", "),
        })
      );
    }

    if (validFiles.length > 0) {
      onUpload(validFiles);
    }
  };

  return (
    <label className="cursor-pointer py-[10px]">
      {label || <Clip data-testid="default-label" width={24} height={24} />}
      <input
        data-testid="upload-image-input"
        type="file"
        accept="image/jpeg,image/png,image/gif,image/webp"
        multiple
        hidden
        onChange={handleUpload}
      />
    </label>
  );
}
