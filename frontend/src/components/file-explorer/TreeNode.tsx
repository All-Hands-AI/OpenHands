import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { twMerge } from "tailwind-merge";
import { RootState } from "#/store";
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

function TreeNode({ path, defaultOpen = false }: TreeNodeProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const [children, setChildren] = React.useState<string[] | null>(null);
  const { selectedFileAbsolutePath } = React.useContext(CodeEditorContext);
  const refreshID = useSelector((state: RootState) => state.code.refreshID);

  const dispatch = useDispatch();

  const fileParts = path.split("/");
  const filename =
    fileParts[fileParts.length - 1] || fileParts[fileParts.length - 2];

  const isDirectory = path.endsWith("/");

  const refreshChildren = async () => {
    if (!isDirectory || !isOpen) {
      setChildren(null);
      return;
    }
    const files = await listFiles(path);
    setChildren(files);
  };

  React.useEffect(() => {
    refreshChildren();
  }, [refreshID, isOpen]);

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
        name={filename}
        type={isDirectory ? "folder" : "file"}
        isOpen={isOpen}
        onClick={handleClick}
      />

      {isOpen && children && (
        <div className="ml-5">
          {children.map((child, index) => (
            <TreeNode key={index} path={`${child}`} />
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
