import { FitAddon } from "@xterm/addon-fit";
import {
  ITerminalAddon,
  ITerminalInitOnlyOptions,
  ITerminalOptions,
  Terminal,
} from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import React from "react";

type CommandType = "input" | "output";
type Command = { type: CommandType; content: string };

interface XTermProps {
  options?: ITerminalOptions & ITerminalInitOnlyOptions;
  commands?: Command[];
  addons?: ITerminalAddon[];
}

function useXTerm({ options, commands, addons }: XTermProps) {
  const [terminal, setTerminal] = React.useState<Terminal | null>(null);
  const [fitAddon] = React.useState<FitAddon>(new FitAddon());
  const xtermRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    /* Create a new terminal instance */
    const xterm = new Terminal(options);
    xterm.loadAddon(fitAddon);
    addons?.forEach((addon) => xterm.loadAddon(addon));

    setTerminal(xterm);

    return () => {
      xterm.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    /* Open the terminal in the DOM */
    if (terminal && xtermRef.current) {
      terminal.open(xtermRef.current);
    }
  }, [terminal, fitAddon]);

  React.useEffect(() => {
    /* Write commands to the terminal */
    if (terminal && commands) {
      commands.forEach((command) => {
        if (command.type === "input") {
          terminal.write("$ ");
          terminal.write(`${command.content}\r`); // \r is needed to move the cursor to the beginning of the line to prevent tabbing the next line
        } else {
          terminal.writeln(command.content);
        }

        terminal.write("\n");
      });

      terminal.write("$ ");
    }
  }, [terminal, commands]);

  React.useEffect(() => {
    /* Resize the terminal when the window is resized */
    let resizeObserver: ResizeObserver;

    if (xtermRef.current) {
      resizeObserver = new ResizeObserver(() => {
        fitAddon.fit();
      });

      resizeObserver.observe(xtermRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [fitAddon]);

  return xtermRef;
}

export default useXTerm;
