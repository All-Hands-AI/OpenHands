import { IDisposable, Terminal as XtermTerminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import React, { useEffect, useRef } from "react";
import { FitAddon } from "xterm-addon-fit";
import socket from "../socket/socket";

class JsonWebsocketAddon {
  _socket: WebSocket;

  _disposables: IDisposable[];

  constructor(_socket: WebSocket) {
    this._socket = _socket;
    this._disposables = [];
  }

  activate(terminal: XtermTerminal) {
    this._disposables.push(
      terminal.onData((data) => {
        const payload = JSON.stringify({ action: "terminal", data });
        this._socket.send(payload);
      }),
    );
    this._socket.addEventListener("message", (event) => {
      const { action, args, observation, content } = JSON.parse(event.data);
      if (action === "run") {
        terminal.writeln(args.command);
      }
      if (observation === "run") {
        content.split("\n").forEach((line: string) => {
          terminal.writeln(line);
        });
        terminal.write("\n$ ");
      }
    });
  }

  dispose() {
    this._disposables.forEach((d) => d.dispose());
    this._socket.removeEventListener("message", () => {});
  }
}

/**
 * The terminal's content is set by write messages. To avoid complicated state logic,
 * we keep the terminal persistently open as a child of <App /> and hidden when not in use.
 */

function Terminal(): JSX.Element {
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const bgColor = getComputedStyle(document.documentElement)
      .getPropertyValue("--bg-workspace")
      .trim();

    const terminal = new XtermTerminal({
      // This value is set to the appropriate value by the
      // `fitAddon.fit()` call below.
      // If not set here, the terminal does not respect the width
      // of its parent element. This causes a bug where the terminal
      // is too large and switching tabs causes a layout shift.
      cols: 0,
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
      theme: {
        background: bgColor,
      },
    });
    terminal.write("$ ");

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    terminal.open(terminalRef.current as HTMLDivElement);

    // Without this timeout, `fitAddon.fit()` throws the error
    // "this._renderer.value is undefined"
    setTimeout(() => {
      fitAddon.fit();
    }, 1);

    const jsonWebsocketAddon = new JsonWebsocketAddon(socket);
    terminal.loadAddon(jsonWebsocketAddon);

    return () => {
      terminal.dispose();
    };
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 text-lg border-b border-border">Terminal</div>
      <div className="grow p-2 flex min-h-0">
        <div ref={terminalRef} className="h-full w-full" />
      </div>
    </div>
  );
}

export default Terminal;
