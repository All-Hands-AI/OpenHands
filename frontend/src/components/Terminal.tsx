import React, { useEffect, useRef } from "react";
import { Terminal as XtermTerminal } from "@xterm/xterm";
import { AttachAddon } from "xterm-addon-attach";
import { FitAddon } from "xterm-addon-fit";
import "@xterm/xterm/css/xterm.css";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function Terminal(): JSX.Element {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalOutput = `> chatbot-ui@2.0.0 prepare
> husky install

husky - Git hooks installed

added 1455 packages, and audited 1456 packages in 1m

295 packages are looking for funding
  run \`npm fund\` for details
  
found 0 vulnerabilities
npm notice
npm notice New minor version of npm available! 10.7.3 -> 10.9.0
...`;

  useEffect(() => {
    const terminal = new XtermTerminal({
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

    if (!process.env.REACT_APP_TERMINAL_WS_URL) {
      throw new Error(
        "The environment variable REACT_APP_TERMINAL_WS_URL is not set. Please set it to the WebSocket URL of the terminal server.",
      );
    }
    const attachAddon = new AttachAddon(
      new WebSocket(process.env.REACT_APP_TERMINAL_WS_URL as string),
    );
    terminal.loadAddon(attachAddon);

    return () => {
      terminal.dispose();
    };
  }, []);

  return (
    // <div className="terminal">
    //   <SyntaxHighlighter language="bash" style={atomDark}>
    //     {terminalOutput}
    //   </SyntaxHighlighter>
    // </div>
    <div ref={terminalRef} style={{ width: "100%", height: "100%" }} />
  );
}

export default Terminal;
