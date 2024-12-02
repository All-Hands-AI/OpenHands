import { IoIosCloudUpload } from "react-icons/io";
import { IconButton } from "./icon-button";

interface UploadIconButtonProps {
  onClick: () => void;
}

export function UploadIconButton({ onClick }: UploadIconButtonProps) {
  return (
    <IconButton
      icon={
        <IoIosCloudUpload
          size={16}
          className="text-neutral-400 hover:text-neutral-100 transition"
        />
      }
      testId="upload"
      ariaLabel="Upload File"
      onClick={onClick}
    />
  );
}
