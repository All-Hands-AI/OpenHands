import React from "react";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";
import { useFiles } from "#/context/files";
import { cn } from "#/utils/utils";
import { useListFiles } from "#/hooks/query/use-list-files";
import { useListFile } from "#/hooks/query/use-list-file";

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
      className="cursor-pointer text-nowrap rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
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

  const isDirectory = path.endsWith("/");

  const { data: paths } = useListFiles({
    path,
    enabled: isDirectory && isOpen,
  });

  const { data: fileContent, refetch } = useListFile({ path });

  React.useEffect(() => {
    if (fileContent) {
      const code = modifiedFiles[path] || files[path];
      if (!code || fileContent !== files[path]) {
        setFileContent(path, fileContent);
      }
    }
  }, [fileContent, path]);

  const fileParts = path.split("/");
  const filename =
    fileParts[fileParts.length - 1] || fileParts[fileParts.length - 2];

  const handleClick = async () => {
    if (isDirectory) setIsOpen((prev) => !prev);
    else {
      setSelectedPath(path);
      await refetch();
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

      {isOpen && paths && (
        <div className="ml-5">
          {paths.map((child, index) => (
            <TreeNode key={index} path={child} />
          ))}
        </div>
      )}
    </div>
  );
}

export default React.memo(TreeNode);
