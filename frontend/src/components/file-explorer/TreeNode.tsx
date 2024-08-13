import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { twMerge } from "tailwind-merge";
import { RootState } from "#/store";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import { listFiles, selectFile } from "#/services/fileService";
import {
  setCode,
  setActiveFilepath,
  addOrUpdateFileState,
} from "#/state/codeSlice";

interface TitleProps {
  name: string;
  type: "folder" | "file";
  isOpen: boolean;
  isUnsaved: boolean;
  onClick: () => void;
}

function Title({ name, type, isOpen, isUnsaved, onClick }: TitleProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
    >
      <div className="flex-shrink-0">
        {type === "folder" && <FolderIcon isOpen={isOpen} />}
        {type === "file" && <FileIcon filename={name} />}
      </div>
      <div className="flex-grow">
        {name}
        {isUnsaved && "*"}
      </div>
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
  const refreshID = useSelector((state: RootState) => state.code.refreshID);
  const activeFilepath = useSelector((state: RootState) => state.code.path);
  const fileStates = useSelector((state: RootState) => state.code.fileStates);
  const fileState = fileStates.find((f) => f.path === path);
  const isUnsaved = fileState?.savedContent !== fileState?.unsavedContent;

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
    (async () => {
      await refreshChildren();
    })();
  }, [refreshID, isOpen]);

  const handleClick = async () => {
    if (isDirectory) {
      setIsOpen((prev) => !prev);
    } else {
      let newFileState = fileStates.find((f) => f.path === path);
      if (!newFileState) {
        const code = await selectFile(path);
        newFileState = { path, savedContent: code, unsavedContent: code };
      }
      dispatch(addOrUpdateFileState(newFileState));
      dispatch(setCode(newFileState.unsavedContent));
      dispatch(setActiveFilepath(path));
    }
  };

  return (
    <div
      className={twMerge(
        "text-sm text-neutral-400",
        path === activeFilepath ? "bg-gray-700" : "",
      )}
    >
      <Title
        name={filename}
        type={isDirectory ? "folder" : "file"}
        isOpen={isOpen}
        isUnsaved={isUnsaved}
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

export default React.memo(TreeNode);
