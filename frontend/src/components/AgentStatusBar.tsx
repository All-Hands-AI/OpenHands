import React from "react";
import { Trans } from "react-i18next";
import i18next from "i18next";

function AgentStatusBar() {
  const { t } = i18next;

  // TODO: Extend the agent status, e.g.:
  // - Agent is typing
  // - Agent is initializing
  // - Agent is thinking
  // - Agent is ready
  // - Agent is not available
  return (
    <div className="flex items-center space-x-3 ml-6">
      <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
      <span className="text-sm text-stone-400">
        <Trans t={t}>CHAT_INTERFACE$INITIALZING_AGENT_LOADING_MESSAGE</Trans>
      </span>
    </div>
  );
}

export default AgentStatusBar;
