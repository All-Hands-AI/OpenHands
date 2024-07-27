import React, { useState } from "react";
import { useSelector } from "react-redux";
import { VscTerminal } from "react-icons/vsc";
import { IoIosArrowUp, IoIosArrowDown } from "react-icons/io";
import { RootState } from "#/store";
import { useTerminal } from "../../hooks/useTerminal";

import "@xterm/xterm/css/xterm.css";
import IconButton from "../IconButton";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const ref = useTerminal(commands);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleCollapse = () => {
    const workspace = document.querySelector(".workspace") as HTMLDivElement;
    if (workspace) {
      if (!isCollapsed) {
        workspace.style.height = "91.5%";
      } else {
        workspace.style.height = "300px";
      }
      setIsCollapsed(!isCollapsed);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-2 text-sm border-b border-neutral-600">
        <VscTerminal />
        Terminal
        <IconButton
          onClick={handleCollapse}
          icon={isCollapsed ? <IoIosArrowUp /> : <IoIosArrowDown />}
          ariaLabel={isCollapsed ? "Open Terminal" : "Close Terminal"}
          style={{ marginLeft: "auto" }}
        />
      </div>
      <div className="grow p-2 flex min-h-0">
        <div ref={ref} className="h-full w-full" />
      </div>
    </div>
  );
}

export default Terminal;
