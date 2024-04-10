import React from "react";
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

interface FileIconProps {
  filename: string;
}

function FileIcon({ filename }: FileIconProps): JSX.Element | null {
  const extension = filename.slice(filename.lastIndexOf(".") + 1);
  switch (extension) {
    case "js":
      return <DiJavascript />;
    case "ts":
      return <DiJavascript />;
    case "py":
      return <FaPython />;
    case "css":
      return <FaCss3 />;
    case "json":
      return <FaList />;
    case "npmignore":
      return <FaNpm />;
    case "html":
      return <FaHtml5 />;
    case "md":
      return <FaMarkdown />;
    default:
      return <FaFile />;
  }
}

export default FileIcon;
