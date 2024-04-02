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
        const payload = JSON.stringify({ action: "terminal", message: data });
        this._socket.send(payload);
      }),
    );
    this._socket.addEventListener("message", (event) => {
      /* 
        TODO this destructure is very fragile, what if we want
        to add new fields? Maybe not though, probably not much 
        more that could be added
      */
      const { term, action, args, observation, content } = JSON.parse(
        event.data,
      );
      if (action === "run") {
        // TODO rewrite with new formatting
        terminal.writeln(args.command);
      }
      if (term === "output") {
        /*
          TODO
          The backend currently rewrites the entire terminal each iteration, 
          super inefficient.  Need to rewrite to only append new lines.
        */
        terminal.clear();
        terminal.write(content);
      }
      if (observation === "run") {
        // content.split("\n").forEach((line: string) => {
        //   terminal.writeln(line);
        // });
        // terminal.write("\n$ ");
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
  const inputLengthRef = useRef<number>(0);

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

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);

    terminal.open(terminalRef.current as HTMLDivElement);

    terminal.onKey((e) => {
      const printable =
        !e.domEvent.altKey && !e.domEvent.ctrlKey && !e.domEvent.metaKey;

      if (e.domEvent.ctrlKey && e.domEvent.key === "c") {
        // TODO go to newline with CTRL+C
        inputLengthRef.current = 0;
      }

      if (printable) {
        if (e.key === "\r") {
          terminal.write("\n");
          inputLengthRef.current = 0;
        } else if (e.key === "\u007F") {
          if (inputLengthRef.current > 0) {
            terminal.write("\b \b");
            inputLengthRef.current -= 1;
          }
        } else {
          terminal.write(e.key);
          inputLengthRef.current += 1;
        }
      }
    });

    // Without this timeout, `fitAddon.fit()` throws the error
    // "this._renderer.value is undefined"
    setTimeout(() => {
      fitAddon.fit();
    }, 1);

    const jsonWebsocketAddon = new JsonWebsocketAddon(socket);
    terminal.loadAddon(jsonWebsocketAddon);

    const initPayload = JSON.stringify({ action: "terminal", message: "init" });
    socket.send(initPayload);

    return () => {
      terminal.dispose();
    };
  }, []);

  return <div ref={terminalRef} className="h-full w-full block" />;
}

export default Terminal;
