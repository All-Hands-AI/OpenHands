import { FaFile } from "react-icons/fa";
import { getExtension } from "#/utils/utils";
import { EXTENSION_ICON_MAP } from "../../extension-icon-map.constant";

interface FileIconProps {
  filename: string;
}

export function FileIcon({ filename }: FileIconProps) {
  const extension = getExtension(filename);
  return EXTENSION_ICON_MAP[extension] || <FaFile />;
}
