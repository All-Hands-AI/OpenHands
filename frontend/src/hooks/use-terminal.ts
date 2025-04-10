import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import React from "react";
import { Command } from "#/state/command-slice";
import { parseTerminalOutput } from "#/utils/parse-terminal-output";

/*
  NOTE: Tests for this hook are indirectly covered by the tests for the XTermTerminal component.
  The reason for this is that the hook exposes a ref that requires a DOM element to be rendered.
*/

interface UseTerminalConfig {
  commands: Command[];
}

const DEFAULT_TERMINAL_CONFIG: UseTerminalConfig = {
  commands: [],
};

// Create a persistent reference that survives component unmounts
// This ensures terminal history is preserved when navigating away and back
const persistentLastCommandIndex = { current: 0 };

export const useTerminal = ({
  commands,
}: UseTerminalConfig = DEFAULT_TERMINAL_CONFIG) => {
  const terminal = React.useRef<Terminal | null>(null);
  const fitAddon = React.useRef<FitAddon | null>(null);
  const ref = React.useRef<HTMLDivElement>(null);
  const lastCommandIndex = persistentLastCommandIndex; // Use the persistent reference

  const createTerminal = () =>
    new Terminal({
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
      theme: {
        background: "#24272E",
      },
    });

  const initializeTerminal = () => {
    if (terminal.current) {
      if (fitAddon.current) terminal.current.loadAddon(fitAddon.current);
      if (ref.current) terminal.current.open(ref.current);
    }
  };

  React.useEffect(() => {
    terminal.current = createTerminal();
    fitAddon.current = new FitAddon();

    if (ref.current) {
      initializeTerminal();

      if (commands.length > 0) {
        for (let i = 0; i < commands.length; i += 1) {
          const { content, type } = commands[i];
          terminal.current?.writeln(
            parseTerminalOutput(content.replaceAll("\n", "\r\n").trim()),
          );

          if (type === "output") {
            terminal.current.write(`\n`);
          }
        }
        lastCommandIndex.current = commands.length;
      }

      terminal.current.write("$ ");
    }

    return () => {
      terminal.current?.dispose();
    };
  }, [commands]);

  React.useEffect(() => {
    /* Write commands to the terminal */
    if (
      terminal.current &&
      commands.length > 0 &&
      lastCommandIndex.current < commands.length
    ) {
      for (let i = lastCommandIndex.current; i < commands.length; i += 1) {
        // eslint-disable-next-line prefer-const
        let { content, type } = commands[i];

        terminal.current?.writeln(
          parseTerminalOutput(content.replaceAll("\n", "\r\n").trim()),
        );

        if (type === "output") {
          terminal.current.write(`\n$ `);
        }
      }

      lastCommandIndex.current = commands.length; // Update the position of the last command
    }
  }, [commands]);

  React.useEffect(() => {
    let resizeObserver: ResizeObserver | null = null;

    resizeObserver = new ResizeObserver(() => {
      fitAddon.current?.fit();
    });

    if (ref.current) {
      resizeObserver.observe(ref.current);
    }

    return () => {
      resizeObserver?.disconnect();
    };
  }, []);

  return ref;
};
