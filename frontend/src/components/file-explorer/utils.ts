import { WorkspaceFile } from "#/services/fileService";

export const removeEmptyNodes = (root: WorkspaceFile): WorkspaceFile => {
  if (root.children) {
    const children = root.children
      .map(removeEmptyNodes)
      .filter((node) => node !== undefined);
    return {
      ...root,
      children: children.length ? children : undefined,
    };
  }
  return root;
};
