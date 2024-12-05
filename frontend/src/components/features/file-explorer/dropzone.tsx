import { useTranslation } from "react-i18next";
import { IoFileTray } from "react-icons/io5";
import { I18nKey } from "#/i18n/declaration";

interface DropzoneProps {
  onDragLeave: () => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
}

export function Dropzone({ onDragLeave, onDrop }: DropzoneProps) {
  const { t } = useTranslation();

  return (
    <div
      data-testid="dropzone"
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onDragOver={(event) => event.preventDefault()}
      className="z-10 absolute flex flex-col justify-center items-center bg-black top-0 bottom-0 left-0 right-0 opacity-65"
    >
      <IoFileTray size={32} />
      <p className="font-bold text-xl">
        {t(I18nKey.EXPLORER$LABEL_DROP_FILES)}
      </p>
    </div>
  );
}
