import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import OpenHands from "#/api/open-hands";
import { useFiles } from "#/context/files";
import { cn } from "#/utils/utils";

interface TitleProps {
  name: string;
  type: "folder" | "file";
  isOpen: boolean;
  onClick: () => void;
}

function Title({ name, type, isOpen, onClick }: TitleProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
    >
      <div className="flex-shrink-0">
        {type === "folder" && <FolderIcon isOpen={isOpen} />}
        {type === "file" && <FileIcon filename={name} />}
      </div>
      <div className="flex-grow">{name}</div>
    </div>
  );
}

interface TreeNodeProps {
  path: string;
  defaultOpen?: boolean;
}

function TreeNode({ path, defaultOpen = false }: TreeNodeProps) {
  const {
    setFileContent,
    modifiedFiles,
    setSelectedPath,
    files,
    selectedPath,
  } = useFiles();
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const [children, setChildren] = React.useState<string[] | null>(null);
  const refreshID = useSelector((state: RootState) => state.code.refreshID);

  const fileParts = path.split("/");
  const filename =
    fileParts[fileParts.length - 1] || fileParts[fileParts.length - 2];

  const isDirectory = path.endsWith("/");

  const refreshChildren = async () => {
    if (!isDirectory || !isOpen) {
      setChildren(null);
      return;
    }

    const token = localStorage.getItem("token");
    if (token) {
      const newChildren = await OpenHands.getFiles(token, path);
      setChildren(newChildren);
    }
  };

  React.useEffect(() => {
    (async () => {
      await refreshChildren();
    })();
  }, [refreshID, isOpen]);

  const handleClick = async () => {
    const token = localStorage.getItem("token");

    if (isDirectory) {
      setIsOpen((prev) => !prev);
    } else if (token) {
      setSelectedPath(path);
      const code = modifiedFiles[path] || files[path];
      const fetchedCode = await OpenHands.getFile(token, path);

      if (!code || fetchedCode !== files[path]) {
        setFileContent(path, fetchedCode);
      }
    }
  };

  return (
    <div
      className={cn(
        "text-sm text-neutral-400",
        path === selectedPath && "bg-gray-700",
      )}
    >
      <button
        type={isDirectory ? "button" : "submit"}
        name="file"
        value={path}
        className="flex items-center justify-between w-full px-1"
      >
        <Title
          name={filename}
          type={isDirectory ? "folder" : "file"}
          isOpen={isOpen}
          onClick={handleClick}
        />

        {modifiedFiles[path] && (
          <div className="w-2 h-2 rounded-full bg-neutral-500" />
        )}
      </button>

      {isOpen && children && (
        <div className="ml-5">
          {children.map((child, index) => (
            <TreeNode key={index} path={child} />
          ))}
        </div>
      )}
    </div>
  );
}

export default React.memo(TreeNode);
