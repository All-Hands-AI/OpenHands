import React from "react";

interface TreeNodeProps {
  node: TreeNode;
  path: string;
  onFileClick: (path: string) => void;
}

function TreeNode({ node, path, onFileClick }: TreeNodeProps) {
  const [isOpen, setIsOpen] = React.useState(true);

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

export default React.memo(TreeNode);
