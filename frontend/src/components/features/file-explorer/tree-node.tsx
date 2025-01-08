import React from "react";
import { useSelector } from "react-redux";

import { useFiles } from "#/context/files";
import { cn } from "#/utils/utils";
import { useListFiles } from "#/hooks/query/use-list-files";
import { useListFile } from "#/hooks/query/use-list-file";
import { Filename } from "./filename";
import { RootState } from "#/store";

interface TreeNodeProps {
  path: string;
  defaultOpen?: boolean;
}

function TreeNode({ path, defaultOpen = false }: TreeNodeProps) {
  const { setFileContent, setSelectedPath, files, selectedPath } = useFiles();
  const [isOpen, setIsOpen] = React.useState(defaultOpen);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const isDirectory = path.endsWith("/");

  const { data: paths } = useListFiles({
    path,
    enabled: isDirectory && isOpen,
  });

  const { data: fileContent, refetch } = useListFile({ path });

  React.useEffect(() => {
    if (fileContent) {
      if (fileContent !== files[path]) {
        setFileContent(path, fileContent);
      }
    }
  }, [fileContent, path]);

  React.useEffect(() => {
    if (selectedPath === path && !isDirectory) {
      refetch();
    }
  }, [curAgentState, selectedPath, path, isDirectory]);

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
        onClick={handleClick}
        className="flex items-center justify-between w-full px-1"
      >
        <Filename
          name={filename}
          type={isDirectory ? "folder" : "file"}
          isOpen={isOpen}
        />
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
