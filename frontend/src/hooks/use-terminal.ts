import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import React from "react";
import { useTranslation } from "react-i18next";
import { Command } from "#/state/command-slice";
import { parseTerminalOutput } from "#/utils/parse-terminal-output";
import { I18nKey } from "#/i18n/declaration";

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

// Custom event for showing the tooltip
export const SHOW_TERMINAL_TOOLTIP_EVENT = 'show-terminal-tooltip';

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
      // Disable user input
      disableStdin: true,
    });

  const initializeTerminal = () => {
    if (terminal.current) {
      if (fitAddon.current) terminal.current.loadAddon(fitAddon.current);
      if (ref.current) terminal.current.open(ref.current);
    }
  };

  // Show tooltip by dispatching a custom event
  const showTooltip = () => {
    // Find the closest tooltip container
    const tooltipContainer = ref.current?.closest('[data-tooltip-container]');
    if (tooltipContainer) {
      // Dispatch custom event to show tooltip
      const event = new CustomEvent(SHOW_TERMINAL_TOOLTIP_EVENT);
      tooltipContainer.dispatchEvent(event);
      
      // Hide tooltip after 3 seconds
      setTimeout(() => {
        const hideEvent = new CustomEvent(SHOW_TERMINAL_TOOLTIP_EVENT, { detail: { hide: true } });
        tooltipContainer.dispatchEvent(hideEvent);
      }, 3000);
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

      // Add event listeners to detect user interaction
      const handleClick = () => {
        showTooltip();
      };

      const handleKeyDown = () => {
        showTooltip();
      };

      ref.current.addEventListener('click', handleClick);
      ref.current.addEventListener('keydown', handleKeyDown);

      return () => {
        terminal.current?.dispose();
        if (ref.current) {
          ref.current.removeEventListener('click', handleClick);
          ref.current.removeEventListener('keydown', handleKeyDown);
        }
      };
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
