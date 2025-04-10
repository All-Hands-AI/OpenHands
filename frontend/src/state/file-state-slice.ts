import { createSlice, PayloadAction } from "@reduxjs/toolkit"

type SliceState = {
  changed: Record<string, boolean>
  currentPathViewed?: string
} // Map<path, changed>

const initialState: SliceState = {
  changed: {},
  currentPathViewed: "",
}

export const fileStateSlice = createSlice({
  name: "fileState",
  initialState,
  reducers: {
    setChanged(
      state,
      action: PayloadAction<{ path: string; changed: boolean }>,
    ) {
      const { path, changed } = action.payload
      state.changed[path] = changed
    },
    setCurrentPathViewed(state, action: PayloadAction<string>) {
      state.currentPathViewed = action.payload
    },
  },
})

export const { setChanged, setCurrentPathViewed } = fileStateSlice.actions
export default fileStateSlice.reducer
