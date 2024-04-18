import React from "react";

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
    <div>
      <div onClick={handleClick}>{node.name}</div>
      {isOpen && node.children && (
        <div className="ml-4">
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
