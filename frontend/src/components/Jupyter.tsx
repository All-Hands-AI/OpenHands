import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import Highlight from 'react-highlight'
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
          <Highlight className="python">{code}</Highlight>
        </pre>
      </div>
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
            {/* <code
            class="language-console">{@html highlightedCode || code.replaceAll("<", "&lt;")}</code
          >< */}
          <Highlight className="markdown">{code}</Highlight>
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
