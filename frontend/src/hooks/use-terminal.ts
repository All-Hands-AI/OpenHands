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

const renderCommand = (command: Command, terminal: Terminal) => {
  const { content, type } = command;

  if (type === "input") {
    terminal.write("$ ");
    terminal.writeln(
      parseTerminalOutput(content.replaceAll("\n", "\r\n").trim()),
    );
  } else {
    terminal.write(`\n`);
    terminal.writeln(
      parseTerminalOutput(content.replaceAll("\n", "\r\n").trim()),
    );
    terminal.write(`\n`);
  }
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

  // Initialize terminal and handle cleanup
  React.useEffect(() => {
    terminal.current = createTerminal();
    fitAddon.current = new FitAddon();

    if (ref.current) {
      initializeTerminal();
      // Render all commands in array
      // This happens when we just switch to Terminal from other tabs
      if (commands.length > 0) {
        for (let i = 0; i < commands.length; i += 1) {
          renderCommand(commands[i], terminal.current);
        }
        lastCommandIndex.current = commands.length;
      }
    }

    return () => {
      terminal.current?.dispose();
    };
  }, [commands]);

  React.useEffect(() => {
    // Render new commands when they are added to the commands array
    if (
      terminal.current &&
      commands.length > 0 &&
      lastCommandIndex.current < commands.length
    ) {
      for (let i = lastCommandIndex.current; i < commands.length; i += 1) {
        renderCommand(commands[i], terminal.current);
      }
      lastCommandIndex.current = commands.length;
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
