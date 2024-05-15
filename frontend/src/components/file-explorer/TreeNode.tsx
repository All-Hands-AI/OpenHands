import React from "react";
import { useDispatch } from "react-redux";
import { twMerge } from "tailwind-merge";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import { listFiles } from "#/services/fileService";
import { setActiveFilepath } from "#/state/codeSlice";
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
  defaultOpen?: boolean;
}

function TreeNode({
  path,
  defaultOpen = false,
}: TreeNodeProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const [children, setChildren] = React.useState<string[] | null>(null);
  const { selectedFileAbsolutePath } = React.useContext(CodeEditorContext);
  const dispatch = useDispatch();

  const getNameFromPath = (path: string) => {
    const parts = path.split("/");
    return parts[parts.length - 1] || parts[parts.length - 2];
  }

  const name = getNameFromPath(path);
  const isDirectory = path.endsWith("/");

  React.useEffect(() => {
    if (isOpen && isDirectory) {
      listFiles(path).then((files) => {
        setChildren(files);
      });
    } else {
      setChildren(null);
    }
  }, [isOpen]);

  const handleClick = () => {
    if (isDirectory) {
      setIsOpen((prev) => !prev);
    } else {
      dispatch(setActiveFilepath(path));
    }
  };

  return (
    <div
      className={twMerge(
        "text-sm text-neutral-400",
        path === selectedFileAbsolutePath ? "bg-gray-700" : "",
      )}
    >
      <Title
        name={getNameFromPath(path)}
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
