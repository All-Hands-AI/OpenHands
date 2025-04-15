import { IoFolder, IoFolderOpen } from "react-icons/io5"

interface FolderIconProps {
  isOpen: boolean
}

export function FolderIcon({ isOpen }: FolderIconProps) {
  return isOpen ? (
    <IoFolderOpen className="icon" />
  ) : (
    // fill-primary-500
    <IoFolder className="icon" />
  )
}
