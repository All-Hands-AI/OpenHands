import { createSlice } from "@reduxjs/toolkit";

export enum ActionSecurityRisk {
  UNKNOWN = -1,
  LOW = 0,
  MEDIUM = 1,
  HIGH = 2,
}

export type SecurityAnalyzerLog = {
  id: number;
  content: string;
  security_risk: ActionSecurityRisk;
  confirmation_state?: "awaiting_confirmation" | "confirmed" | "rejected";
  confirmed_changed: boolean;
};

const initialLogs: SecurityAnalyzerLog[] = [];

export const securityAnalyzerSlice = createSlice({
  name: "securityAnalyzer",
  initialState: {
    logs: initialLogs,
  },
  reducers: {
    appendSecurityAnalyzerInput: (state, action) => {
      const log = {
        id: action.payload.id,
        content:
          action.payload.args.command ||
          action.payload.args.code ||
          action.payload.args.content ||
          action.payload.message,
        security_risk: action.payload.args.security_risk as ActionSecurityRisk,
        confirmation_state: action.payload.args.confirmation_state,
        confirmed_changed: false,
      };

      const existingLog = state.logs.find(
        (stateLog) =>
          stateLog.id === log.id ||
          (stateLog.confirmation_state === "awaiting_confirmation" &&
            stateLog.content === log.content),
      );

      if (existingLog) {
        if (existingLog.confirmation_state !== log.confirmation_state) {
          existingLog.confirmation_state = log.confirmation_state;
          existingLog.confirmed_changed = true;
        }
      } else {
        state.logs.push(log);
      }
    },
  },
});

export const { appendSecurityAnalyzerInput } = securityAnalyzerSlice.actions;

export default securityAnalyzerSlice.reducer;
