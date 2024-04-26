import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import SyntaxHighlighter from 'react-syntax-highlighter';
import Markdown from 'react-markdown';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { Cell } from "#/state/jupyterSlice";

interface IJupyterCell {
  cell: Cell;
}

function JupyterCell({ cell }: IJupyterCell): JSX.Element {
  const code = cell.content;

  if (cell.type === "input") {
    return (
      <div className={"rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs"}>
        <div className={"mb-1 text-gray-400"}>EXECUTE</div>
        <pre
          className={"scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5"}
          style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
        >
          <SyntaxHighlighter language="python" style={atomOneDark}>
            {code}
          </SyntaxHighlighter>
        </pre>
      </div >
    );
  }
  else {
    return (
      <div className={"rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs"}>
        <div className={"mb-1 text-gray-400"}>STDOUT/STDERR</div>
        <pre
          className={"scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5 max-h-[60vh] bg-gray-800"}
          style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
        >
          {/* split code by newline and render each line as a plaintext, except it starts with `![image]` so we render it as markdown */}
          {code.split("\n").map((line, index) => {
            if (line.startsWith("![image](data:image/png;base64,")) {
              // return <Markdown key={index}>{line.slice(2, -1)}</Markdown>;
              // add new line before and after the image
              return (
                <div key={index}>
                  <Markdown urlTransform={(value: string) => value}>
                    {line}
                  </Markdown>
                  <br />
                </div>
              );
            }
            return (
              <div key={index}>
                <SyntaxHighlighter language="plaintext" style={atomOneDark}>{line}</SyntaxHighlighter>
                <br />
              </div>
            )
          })}
        </pre>
      </div>
    );
  }
}

function Jupyter(): JSX.Element {
  const { cells } = useSelector(
    (state: RootState) => state.jupyter,
  );

  return (
    <div className="flex-1 overflow-y-auto flex flex-col">
      {cells.map((cell, index) => (
        <JupyterCell key={index} cell={cell} />
      ))}
    </div>
  );
}


export default Jupyter;
