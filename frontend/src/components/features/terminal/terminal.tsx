import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { Tooltip } from "@heroui/react";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const [showTooltip, setShowTooltip] = useState(false);
  const { t } = useTranslation();
  
  const ref = useTerminal({
    commands,
  });

  // Show tooltip when user clicks or tries to interact with terminal
  const handleTerminalClick = () => {
    setShowTooltip(true);
    // Hide tooltip after 5 seconds
    setTimeout(() => setShowTooltip(false), 5000);
  };

  const handleTerminalKeyDown = () => {
    setShowTooltip(true);
    // Hide tooltip after 5 seconds
    setTimeout(() => setShowTooltip(false), 5000);
  };

  return (
    <div className="h-full p-2 min-h-0 flex-grow">
      <Tooltip 
        content={
          <div className="max-w-xs">
            {t(I18nKey.TERMINAL$TOOLTIP_READ_ONLY)}
          </div>
        } 
        placement="bottom"
        open={showTooltip}
      >
        <div 
          ref={ref} 
          className="h-full w-full cursor-not-allowed" 
          onClick={handleTerminalClick}
          onKeyDown={handleTerminalKeyDown}
          tabIndex={0}
        />
      </Tooltip>
    </div>
  );
}

export default Terminal;
