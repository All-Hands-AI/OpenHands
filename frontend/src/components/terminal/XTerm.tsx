import {
  ITerminalInitOnlyOptions,
  ITerminalOptions,
  Terminal,
} from "@xterm/xterm";
import React from "react";

type CommandType = "input" | "output";
type Command = { type: CommandType; content: string };

interface XTermProps {
  options?: ITerminalOptions & ITerminalInitOnlyOptions;
  commands?: Command[];
}

function XTerm({ options, commands }: XTermProps) {
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
    }
  }, [terminal]);

  React.useEffect(() => {
    if (terminal && commands) {
      commands.forEach((command) => {
        if (command.type === "input") {
          terminal.write("$ ");
          terminal.write(`${command.content}\n\r`); // \r is needed to move the cursor to the beginning of the line to prevent tabbing the next line
        } else {
          terminal.writeln(command.content);
        }

        terminal.write("\n");
      });
    }
  }, [terminal, commands]);

  return (
    <div>
      <div ref={xtermRef} />
    </div>
  );
}

XTerm.defaultProps = {
  options: undefined,
  commands: [],
};

export default XTerm;
