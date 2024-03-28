import React, { useEffect, useRef } from "react";
import { IDisposable, Terminal as XtermTerminal } from "@xterm/xterm";
import { FitAddon } from "xterm-addon-fit";
import "@xterm/xterm/css/xterm.css";
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
        const printCommand = () => {
          terminal.writeln(args.command);
        };

        // Adjust delay before printing the command
        setTimeout(printCommand, 50);
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

type TerminalProps = {
  hidden: boolean;
};

function Terminal({ hidden }: TerminalProps): JSX.Element {
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const terminal = new XtermTerminal({
      cols: 0,
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
    });

    terminal.write("$ ");

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    if (terminalRef.current) {
      terminal.open(terminalRef.current);
    }

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
    <div ref={terminalRef} style={{ display: hidden ? "none" : "block" }} />
  );
}

export default Terminal;
