import { createSlice } from "@reduxjs/toolkit"

export const initialState = {
  computerList: [],
  eventID: null,
}

export const computerSlice = createSlice({
  name: "computer",
  initialState,
  reducers: {
    setComputerList: (state, action) => {
      state.computerList.push(action.payload)
    },
    setEventID: (state, action) => {
      state.eventID = action.payload
    },
    clearComputerList: (state) => {
      state.computerList = []
    },
  },
})

export const { setComputerList, setEventID, clearComputerList } = computerSlice.actions

export default computerSlice.reducer
