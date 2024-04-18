import { createSlice } from "@reduxjs/toolkit";
import { WorkspaceItem } from "../services/fileService";

function addItemsToWorkspace(
  items: WorkspaceItem[],
  workspace: WorkspaceItem[],
): WorkspaceItem[] {
  const filteredItems = items.filter(
    (item) => !workspace.find((file) => file.id === item.id),
  );
  if (filteredItems.length === 0) {
    return workspace;
  }
  for (const item of filteredItems) {
    const parentItem = workspace.find((file) => file.id === item.parent);
    if (!parentItem) {
      return workspace;
    }
    parentItem.children = [...parentItem.children, item.id];
  }
  return [...workspace, ...filteredItems];
}

export const codeSlice = createSlice({
  name: "code",
  initialState: {
    code: "# Welcome to OpenDevin!",
    selectedIds: [] as string[],
    workspaceFolder: [
      {
        name: "",
        children: [],
        isBranch: true,
        relativePath: "",
        id: "root",
        parent: null,
      },
    ] as WorkspaceItem[],
  },
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
    resetWorkspace: (state) => {
      state.workspaceFolder = [
        {
          name: "",
          children: [],
          isBranch: true,
          relativePath: "",
          id: "root",
          parent: null,
        },
      ];
    },
    updateWorkspace: (state, action) => {
      state.workspaceFolder = addItemsToWorkspace(
        action.payload as WorkspaceItem[],
        state.workspaceFolder,
      );
    },
    pruneWorkspace: (state, action) => {
      const item = action.payload as WorkspaceItem;
      state.workspaceFolder = [
        ...state.workspaceFolder.filter((file) => !file.id.includes(item.id)),
        { ...item, children: [] },
      ];
    },
  },
});

export const { setCode, updateWorkspace, pruneWorkspace, resetWorkspace } =
  codeSlice.actions;

export default codeSlice.reducer;
