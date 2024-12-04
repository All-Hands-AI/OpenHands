import { FaFolder, FaFolderOpen } from "react-icons/fa";

interface FolderIconProps {
  isOpen: boolean;
}

export function FolderIcon({ isOpen }: FolderIconProps): JSX.Element {
  return isOpen ? (
    <FaFolderOpen color="D9D3D0" className="icon" />
  ) : (
    <FaFolder color="D9D3D0" className="icon" />
  );
}
