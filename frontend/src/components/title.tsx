import { FolderIcon } from "./folder-icon";
import { FileIcon } from "./file-icons";

interface TitleProps {
  name: string;
  type: "folder" | "file";
  isOpen: boolean;
  onClick: () => void;
}

export function Title({ name, type, isOpen, onClick }: TitleProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer text-nowrap rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
    >
      <div className="flex-shrink-0">
        {type === "folder" && <FolderIcon isOpen={isOpen} />}
        {type === "file" && <FileIcon filename={name} />}
      </div>
      <div className="flex-grow">{name}</div>
    </div>
  );
}
