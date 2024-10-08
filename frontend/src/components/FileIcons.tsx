import { DiJavascript } from "react-icons/di";
import {
  FaCss3,
  FaFile,
  FaHtml5,
  FaList,
  FaMarkdown,
  FaNpm,
  FaPython,
} from "react-icons/fa";
import { getExtension } from "#/utils/utils";

const EXTENSION_ICON_MAP: Record<string, JSX.Element> = {
  js: <DiJavascript />,
  ts: <DiJavascript />,
  py: <FaPython />,
  css: <FaCss3 />,
  json: <FaList />,
  npmignore: <FaNpm />,
  html: <FaHtml5 />,
  md: <FaMarkdown />,
};

interface FileIconProps {
  filename: string;
}

function FileIcon({ filename }: FileIconProps) {
  const extension = getExtension(filename);
  return EXTENSION_ICON_MAP[extension] || <FaFile />;
}

export default FileIcon;
