import React from "react";
import { twMerge } from "tailwind-merge";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import { WorkspaceFile, listFiles } from "#/services/fileService";
import { CodeEditorContext } from "../CodeEditorContext";

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
      {type === "folder" && <FolderIcon isOpen={isOpen} />}
      {type === "file" && <FileIcon filename={name} />}
      {name}
    </div>
  );
}

interface TreeNodeProps {
  path: string;
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function TreeNode({
  path,
  onFileClick,
  defaultOpen = false,
}: TreeNodeProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const [isDirectory, setIsDirectory] = React.useState(false);
  const [children, setChildren] = React.useState<string[] | null>(null);
  const { selectedFileAbsolutePath } = React.useContext(CodeEditorContext);

  React.useEffect(() => {
    const isDir = path.endsWith("/");
    setIsDirectory(isDir);
  }, [path]);

  React.useEffect(() => {
    if (isOpen) {
      listFiles(path).then((files) => {
        setChildren(files);
      });
    } else {
      setChildren(null);
    }
  }, [isOpen]);

  const handleClick = React.useCallback(() => {
    if (self.isDirectory) {
      setIsOpen((prev) => !prev);
    } else {
      onFileClick(path);
    }
  }, [path, onFileClick]);

  return (
    <div
      className={twMerge(
        "text-sm text-neutral-400",
        path === selectedFileAbsolutePath ? "bg-gray-700" : "",
      )}
    >
      <Title
        name={path}
        type={isDirectory ? "folder" : "file"}
        isOpen={isOpen}
        onClick={handleClick}
      />

      {isOpen && children && (
        <div className="ml-5">
          {children.map((child, index) => (
            <TreeNode
              key={index}
              path={`${child}`}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}

TreeNode.defaultProps = {
  defaultOpen: false,
};

export default React.memo(TreeNode);
