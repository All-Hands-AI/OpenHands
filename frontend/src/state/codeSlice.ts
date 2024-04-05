import { createSlice } from "@reduxjs/toolkit";
import { INode, flattenTree } from "react-accessible-treeview";
import { IFlatMetadata } from "react-accessible-treeview/dist/TreeView/utils";
import { WorkspaceFile } from "../services/fileService";

export const codeSlice = createSlice({
  name: "code",
  initialState: {
    code: "# Welcome to OpenDevin!",
    selectedIds: [] as number[],
    workspaceFolder: { name: "" } as WorkspaceFile,
  },
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
    updatePath: (state, action) => {
      const path = action.payload;
      const pathParts = path.split("/");
      let current = state.workspaceFolder;

      for (let i = 0; i < pathParts.length - 1; i += 1) {
        const folderName = pathParts[i];
        let folder = current.children?.find((file) => file.name === folderName);

        if (!folder) {
          folder = { name: folderName, children: [] };
          current.children?.push(folder);
        }

        current = folder;
      }

      const fileName = pathParts[pathParts.length - 1];
      if (!current.children?.find((file) => file.name === fileName)) {
        current.children?.push({ name: fileName });
      }

      const data = flattenTree(state.workspaceFolder);
      const checkPath: (
        file: INode<IFlatMetadata>,
        pathIndex: number,
      ) => boolean = (file, pathIndex) => {
        if (pathIndex < 0) {
          if (file.parent === null) return true;
          return false;
        }
        if (pathIndex >= 0 && file.name !== pathParts[pathIndex]) {
          return false;
        }
        return checkPath(
          data.find((f) => f.id === file.parent)!,
          pathIndex - 1,
        );
      };
      const selected = data
        .filter((file) => checkPath(file, pathParts.length - 1))
        .map((file) => file.id) as number[];
      state.selectedIds = selected;
    },
    updateWorkspace: (state, action) => {
      state.workspaceFolder = action.payload;
    },
  },
});

export const { setCode, updatePath, updateWorkspace } = codeSlice.actions;

export default codeSlice.reducer;
