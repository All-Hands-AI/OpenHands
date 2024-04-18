export const removeEmptyNodes = (tree: TreeNode[]): TreeNode[] =>
  tree.map((node) => {
    if (node.children) {
      const children = removeEmptyNodes(node.children);
      return {
        ...node,
        children: children.length ? children : undefined,
      };
    }
    return node;
  });
