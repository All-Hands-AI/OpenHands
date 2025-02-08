import { DiJavascript } from "react-icons/di";
import {
  FaCss3,
  FaHtml5,
  FaList,
  FaMarkdown,
  FaNpm,
  FaPython,
} from "react-icons/fa";

export const EXTENSION_ICON_MAP: Record<string, React.ReactNode> = {
  js: <DiJavascript />,
  ts: <DiJavascript />,
  py: <FaPython />,
  css: <FaCss3 />,
  json: <FaList />,
  npmignore: <FaNpm />,
  html: <FaHtml5 />,
  md: <FaMarkdown />,
};
