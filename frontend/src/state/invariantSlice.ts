import { createSlice } from "@reduxjs/toolkit";

export enum ActionSecurityRisk {
  UNKNOWN = -1,
  LOW = 0,
  MEDIUM = 1,
  HIGH = 2,
}

export type Invariant = {
  content: string;
  security_risk: ActionSecurityRisk;
  is_confirmed?: "awaiting_confirmation" | "confirmed" | "rejected";
  confirmed_changed: boolean;
};

const initialLogs: Invariant[] = [];

export const invariantSlice = createSlice({
  name: "invariant",
  initialState: {
    logs: initialLogs,
  },
  reducers: {
    appendInvariantInput: (state, action) => {
      const log = {
        content:
          action.payload.command ||
          action.payload.code ||
          action.payload.content,
        security_risk: action.payload.security_risk as ActionSecurityRisk,
        is_confirmed: action.payload.is_confirmed,
        confirmed_changed: false,
      };
      const lastLog = state.logs[state.logs.length - 1];
      const isDuplicateLog =
        lastLog &&
        lastLog.content === log.content &&
        lastLog.is_confirmed === "awaiting_confirmation" &&
        log.is_confirmed !== lastLog.is_confirmed;

      if (!isDuplicateLog) {
        state.logs.push(log);
      } else {
        lastLog.is_confirmed = log.is_confirmed;
        lastLog.confirmed_changed = true;
      }
    },
  },
});

export const { appendInvariantInput } = invariantSlice.actions;

export default invariantSlice.reducer;
