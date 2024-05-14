import React from "react";
import { twMerge } from "tailwind-merge";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import { WorkspaceFile } from "#/services/fileService";
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
  node: WorkspaceFile;
  path: string;
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function TreeNode({
  node,
  path,
  onFileClick,
  defaultOpen = false,
}: TreeNodeProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const { selectedFileAbsolutePath } = React.useContext(CodeEditorContext);

  const handleClick = React.useCallback(() => {
    if (node.children) {
      setIsOpen((prev) => !prev);
    } else {
      onFileClick(path);
    }
  }, [node, path, onFileClick]);

  return (
    <div
      className={twMerge(
        "text-sm text-neutral-400",
        path === selectedFileAbsolutePath ? "bg-gray-700" : "",
      )}
    >
      <Title
        name={node.name}
        type={node.children ? "folder" : "file"}
        isOpen={isOpen}
        onClick={handleClick}
      />

      {isOpen && node.children && (
        <div className="ml-5">
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              path={`${path}/${child.name}`}
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
