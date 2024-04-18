import React from "react";
import FolderIcon from "../FolderIcon";
import FileIcon from "../FileIcons";

interface TreeNodeProps {
  node: TreeNode;
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

  const handleClick = React.useCallback(() => {
    if (node.children) {
      setIsOpen((prev) => !prev);
    } else {
      onFileClick(path);
    }
  }, [node, path, onFileClick]);

  return (
    <div className="text-sm text-neutral-400">
      <div
        onClick={handleClick}
        className="cursor-pointer rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
      >
        {node.children ? (
          <FolderIcon isOpen={isOpen} />
        ) : (
          <FileIcon filename={node.name} />
        )}
        {node.name}
      </div>
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
