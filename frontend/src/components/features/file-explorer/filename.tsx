import { FolderIcon } from "./folder-icon"
import { FileIcon } from "./file-icon"
import { useDispatch } from "react-redux"
import { setCurrentPathViewed } from "#/state/file-state-slice"
import path from "path"

interface FilenameProps {
  name: string
  path: string
  type: "folder" | "file"
  isOpen: boolean
}

export function Filename({ name, type, isOpen, path }: FilenameProps) {
  const dispatch = useDispatch()

  return (
    <div
      onClick={() => dispatch(setCurrentPathViewed(path))}
      className="nowrap flex cursor-pointer items-center gap-2 text-nowrap rounded-[5px] p-1"
    >
      <div className="flex-shrink-0">
        {type === "folder" && <FolderIcon isOpen={isOpen} />}
        {type === "file" && <FileIcon filename={name} />}
      </div>
      <div className="flex-grow">{name}</div>
    </div>
  )
}
