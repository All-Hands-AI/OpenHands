import { useSelector } from "react-redux";
import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import React from "react";
import { RootState } from "#/store";
import { SHOW_TERMINAL_TOOLTIP_EVENT, useTerminal } from "#/hooks/use-terminal";
import { I18nKey } from "#/i18n/declaration";
import "@xterm/xterm/css/xterm.css";

function Terminal() {
  const { t } = useTranslation();
  const { commands } = useSelector((state: RootState) => state.cmd);
  const [showTooltip, setShowTooltip] = React.useState(false);
  const tooltipContainerRef = React.useRef<HTMLDivElement>(null);

  const ref = useTerminal({
    commands,
  });

  // Handle custom event to show/hide tooltip
  React.useEffect(() => {
    const container = tooltipContainerRef.current;
    
    if (container) {
      const handleShowTooltip = (event: Event) => {
        const customEvent = event as CustomEvent;
        if (customEvent.detail?.hide) {
          setShowTooltip(false);
        } else {
          setShowTooltip(true);
        }
      };
      
      container.addEventListener(SHOW_TERMINAL_TOOLTIP_EVENT, handleShowTooltip);
      
      return () => {
        container.removeEventListener(SHOW_TERMINAL_TOOLTIP_EVENT, handleShowTooltip);
      };
    }
  }, []);

  return (
    <div className="h-full p-2 min-h-0 flex-grow">
      <div ref={tooltipContainerRef} data-tooltip-container>
        <Tooltip 
          content={t(I18nKey.TERMINAL$TOOLTIP_READ_ONLY)} 
          open={showTooltip}
          placement="top-end"
        >
          <div ref={ref} className="h-full w-full" />
        </Tooltip>
      </div>
    </div>
  );
}

export default Terminal;
