import {
  ITerminalInitOnlyOptions,
  ITerminalOptions,
  Terminal,
} from "@xterm/xterm";
import React from "react";

interface XTermProps {
  options?: ITerminalOptions & ITerminalInitOnlyOptions;
}

function XTerm({ options }: XTermProps) {
  const [terminal, setTerminal] = React.useState<Terminal | null>(null);
  const xtermRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const xterm = new Terminal(options);
    setTerminal(xterm);

    return () => {
      xterm.dispose();
    };
  }, [options]);

  React.useEffect(() => {
    if (terminal && xtermRef.current) {
      terminal.open(xtermRef.current);
      terminal.write("$ ");
    }
  }, [terminal]);

  return (
    <div>
      <div ref={xtermRef} />
    </div>
  );
}

XTerm.defaultProps = {
  options: undefined,
};

export default XTerm;
