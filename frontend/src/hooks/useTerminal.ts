import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import React from "react";
import { Command } from "#/state/commandSlice";

/*
  NOTE: Tests for this hook are indirectly covered by the tests for the XTermTerminal component.
  The reason for this is that the hook exposes a ref that requires a DOM element to be rendered.
*/

export const useTerminal = (commands: Command[] = []) => {
  const terminal = React.useRef<Terminal | null>(null);
  const fitAddon = React.useRef<FitAddon | null>(null);
  const ref = React.useRef<HTMLDivElement>(null);
  const lastCommandIndex = React.useRef(0);

  React.useEffect(() => {
    /* Create a new terminal instance */
    terminal.current = new Terminal({
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
      theme: {
        background: "#262626",
      },
    });
    fitAddon.current = new FitAddon();

    let resizeObserver: ResizeObserver;

    if (ref.current) {
      /* Initialize the terminal in the DOM */
      terminal.current.loadAddon(fitAddon.current);
      terminal.current.open(ref.current);

      terminal.current.write("$ ");

      /* Listen for resize events */
      resizeObserver = new ResizeObserver(() => {
        fitAddon.current?.fit();
      });
      resizeObserver.observe(ref.current);
    }

    return () => {
      terminal.current?.dispose();
      resizeObserver.disconnect();
    };
  }, []);

  React.useEffect(() => {
    /* Write commands to the terminal */
    if (terminal.current && commands.length > 0) {
      // Start writing commands from the last command index
      for (let i = lastCommandIndex.current; i < commands.length; i += 1) {
        const command = commands[i];
        const lines = command.content.split("\n");

        lines.forEach((line: string) => {
          terminal.current?.writeln(line);
        });

        if (command.type === "output") {
          terminal.current.write("\n$ ");
        }
      }

      lastCommandIndex.current = commands.length; // Update the position of the last command
    }
  }, [commands]);

  return ref;
};
