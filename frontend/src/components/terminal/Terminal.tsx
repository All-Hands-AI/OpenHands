import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "../../hooks/useTerminal";

import "@xterm/xterm/css/xterm.css";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const ref = useTerminal(commands);

  return (
    <div className="h-full p-2 min-h-0">
      <div ref={ref} className="h-full w-full" />
    </div>
  );
}

export default Terminal;
