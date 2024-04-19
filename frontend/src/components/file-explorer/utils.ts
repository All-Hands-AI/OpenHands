import { WorkspaceFile } from "../../services/fileService";

export const removeEmptyNodes = (tree: WorkspaceFile[]): WorkspaceFile[] =>
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
