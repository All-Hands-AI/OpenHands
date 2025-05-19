import { createSlice } from "@reduxjs/toolkit";

export type Cell = {
  content: string;
  type: "input" | "output";
  imageUrls?: string[];
};

const initialCells: Cell[] = [];

export const jupyterSlice = createSlice({
  name: "jupyter",
  initialState: {
    cells: initialCells,
  },
  reducers: {
    appendJupyterInput: (state, action) => {
      state.cells.push({ content: action.payload, type: "input" });
    },
    appendJupyterOutput: (state, action) => {
      state.cells.push({
        content: action.payload.content,
        type: "output",
        imageUrls: action.payload.imageUrls,
      });
    },
    clearJupyter: (state) => {
      state.cells = [];
    },
  },
});

export const { appendJupyterInput, appendJupyterOutput, clearJupyter } =
  jupyterSlice.actions;

export const jupyterReducer = jupyterSlice.reducer;
export default jupyterReducer;
