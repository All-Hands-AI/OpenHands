import React, { useEffect, useRef } from "react";
import { IDisposable, Terminal as XtermTerminal } from "@xterm/xterm";
import { FitAddon } from "xterm-addon-fit";
import "@xterm/xterm/css/xterm.css";

class JsonWebsocketAddon {
  _socket: WebSocket;

  _disposables: IDisposable[];

  constructor(socket: WebSocket) {
    this._socket = socket;
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
      const { message } = JSON.parse(event.data);
      if (message.action === "terminal") {
        terminal.write(message.data);
      }
    });
  }

  dispose() {
    this._disposables.forEach((d) => d.dispose());
    this._socket.removeEventListener("message", () => {});
  }
}

function Terminal(): JSX.Element {
  const terminalRef = useRef<HTMLDivElement>(null);
  const WS_URL = import.meta.env.VITE_TERMINAL_WS_URL;
  useEffect(() => {
    const terminal = new XtermTerminal({
      // This value is set to the appropriate value by the
      // `fitAddon.fit()` call below.
      // If not set here, the terminal does not respect the width
      // of its parent element. This causes a bug where the terminal
      // is too large and switching tabs causes a layout shift.
      cols: 0,
      fontFamily: "Menlo, Monaco, 'Courier New', monospace",
      fontSize: 14,
    });

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    terminal.open(terminalRef.current as HTMLDivElement);

    // Without this timeout, `fitAddon.fit()` throws the error
    // "this._renderer.value is undefined"
    setTimeout(() => {
      fitAddon.fit();
    }, 1);

    if (!WS_URL) {
      throw new Error(
        "The environment variable VITE_TERMINAL_WS_URL is not set. Please set it to the WebSocket URL of the terminal server.",
      );
    }
    const socket = new WebSocket(WS_URL as string);
    const jsonWebsocketAddon = new JsonWebsocketAddon(socket);
    terminal.loadAddon(jsonWebsocketAddon);

    return () => {
      terminal.dispose();
    };
  }, []);

  return <div ref={terminalRef} style={{ width: "100%", height: "100%" }} />;
}

export default Terminal;
