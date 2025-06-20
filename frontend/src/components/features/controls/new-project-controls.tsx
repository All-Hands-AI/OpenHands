import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import {
  AGENT_STATUS_MAP,
  IndicatorColor,
} from "../../agent-status-map.constant";
import { SecurityLock } from "./security-lock";

// Simplified AgentControlBar that doesn't depend on conversation data
function SimpleAgentControlBar() {
  console.log("🔍 [DEBUG] SimpleAgentControlBar component starting...");

  return (
    <div className="flex items-center gap-2">
      <button
        className="px-3 py-1 bg-base-secondary text-content rounded-lg text-sm border border-border hover:bg-base-tertiary transition-colors"
        disabled
      >
        Start Agent
      </button>
      <button
        className="px-3 py-1 bg-base-secondary text-content rounded-lg text-sm border border-border hover:bg-base-tertiary transition-colors"
        disabled
      >
        Stop Agent
      </button>
    </div>
  );
}

// Simplified AgentStatusBar that doesn't depend on conversation data
function SimpleAgentStatusBar() {
  console.log("🔍 [DEBUG] SimpleAgentStatusBar component starting...");

  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  console.log("🔍 [DEBUG] SimpleAgentStatusBar - Agent state:", curAgentState);

  const statusMessage = AGENT_STATUS_MAP[curAgentState]?.message || I18nKey.CHAT_INTERFACE$AGENT_STOPPED_MESSAGE;
  const indicatorColor = AGENT_STATUS_MAP[curAgentState]?.indicator || IndicatorColor.RED;

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center px-2 py-1 text-gray-400 rounded-[100px] text-sm gap-[6px]">
        <div
          className={`w-2 h-2 rounded-full animate-pulse ${indicatorColor}`}
        />
        <span className="text-sm text-stone-400">{t(statusMessage)}</span>
      </div>
    </div>
  );
}

interface NewProjectControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

// export function NewProjectControls({ setSecurityOpen, showSecurityLock }: NewProjectControlsProps) {
//   console.log("🔍 [DEBUG] NewProjectControls component starting...");
//   console.log("🔍 [DEBUG] NewProjectControls - showSecurityLock:", showSecurityLock);

//   return (
//     <div className="flex flex-col gap-2 md:items-center md:justify-between md:flex-row">
//       <div className="flex items-center gap-2">
//         <SimpleAgentControlBar />
//         <SimpleAgentStatusBar />

//         {showSecurityLock && (
//           <SecurityLock onClick={() => setSecurityOpen(true)} />
//         )}
//       </div>

//       {/* Simplified project card */}
//       <div className="bg-base-secondary rounded-lg border border-border p-3 min-w-[200px]">
//         <div className="flex items-center justify-between">
//           <div>
//             <h3 className="font-medium text-content">New Project</h3>
//             <p className="text-xs text-content-secondary">Experimental Interface</p>
//           </div>
//           <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
//         </div>
//       </div>
//     </div>
//   );
// }

// Temporary placeholder component that returns null to hide the bottom area
export function NewProjectControls({ setSecurityOpen, showSecurityLock }: NewProjectControlsProps) {
  return null;
}
