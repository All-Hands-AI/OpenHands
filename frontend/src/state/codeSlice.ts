import { createSlice } from "@reduxjs/toolkit";
import { INode, flattenTree } from "react-accessible-treeview";
import { IFlatMetadata } from "react-accessible-treeview/dist/TreeView/utils";

export const initialState = {
  code: "",
  selectedIds: [] as number[],
};

export const codeSlice = createSlice({
  name: "code",
  initialState,
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
    setActiveFilepath: (state, action) => {
      state.path = action.payload;
    },
  },
});

export const { setCode, setActiveFilepath } = codeSlice.actions;

export default codeSlice.reducer;
