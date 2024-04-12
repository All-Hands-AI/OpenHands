import React from "react";
import { FaFolder, FaFolderOpen } from "react-icons/fa";

interface FolderIconProps {
  isOpen: boolean;
}

function FolderIcon({ isOpen }: FolderIconProps): JSX.Element {
  return isOpen ? (
    <FaFolderOpen color="D9D3D0" className="icon" />
  ) : (
    <FaFolder color="D9D3D0" className="icon" />
  );
}

export default FolderIcon;
