import React, { useRef } from "react";
import SyntaxHighlighter from "react-syntax-highlighter";
import Markdown from "react-markdown";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { VscArrowDown } from "react-icons/vsc";
import { useTranslation } from "react-i18next";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import { I18nKey } from "#/i18n/declaration";
import { useSession } from "#/context/session";
import { extractJupyterCells } from "#/utils/extractJupyterCells";

// TODO: Type this
type Cell = any;

interface IJupyterCell {
  cell: Cell;
}

function JupyterCell({ cell }: IJupyterCell): JSX.Element {
  const code = cell.content;

  if (cell.type === "input") {
    return (
      <div className="rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs">
        <div className="mb-1 text-gray-400">EXECUTE</div>
        <pre
          className="scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5"
          style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
        >
          <SyntaxHighlighter language="python" style={atomOneDark}>
            {code}
          </SyntaxHighlighter>
        </pre>
      </div>
    );
  }

  // aggregate all the NON-image lines into a single plaintext.
  const lines: { type: "plaintext" | "image"; content: string }[] = [];
  let current = "";
  for (const line of code.split("\n")) {
    if (line.startsWith("![image](data:image/png;base64,")) {
      lines.push({ type: "plaintext", content: current });
      lines.push({ type: "image", content: line });
      current = "";
    } else {
      current += `${line}\n`;
    }
  }
  lines.push({ type: "plaintext", content: current });

  return (
    <div className="rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs">
      <div className="mb-1 text-gray-400">STDOUT/STDERR</div>
      <pre
        className="scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5 max-h-[60vh] bg-gray-800"
        style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
      >
        {/* display the lines as plaintext or image */}
        {lines.map((line, index) => {
          if (line.type === "image") {
            return (
              <div key={index}>
                <Markdown urlTransform={(value: string) => value}>
                  {line.content}
                </Markdown>
              </div>
            );
          }
          return (
            <div key={index}>
              <SyntaxHighlighter language="plaintext" style={atomOneDark}>
                {line.content}
              </SyntaxHighlighter>
            </div>
          );
        })}
      </pre>
    </div>
  );
}

function Jupyter(): JSX.Element {
  const { t } = useTranslation();
  const { eventLog } = useSession();
  const [cells, setCells] = React.useState<Cell[]>([]);
  const jupyterRef = useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const simplifiedCells = extractJupyterCells(
      eventLog.map((msg) => JSON.parse(msg)),
    );
    setCells(simplifiedCells);
  }, [eventLog]);

  const { hitBottom, scrollDomToBottom, onChatBodyScroll } =
    useScrollToBottom(jupyterRef);

  return (
    <div className="flex-1">
      <div
        className="overflow-y-auto h-full"
        ref={jupyterRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
      >
        {cells.map((cell, index) => (
          <JupyterCell key={index} cell={cell} />
        ))}
      </div>
      {!hitBottom && (
        <div className="sticky bottom-2 flex items-center justify-center">
          <button
            type="button"
            className="relative border-1 text-sm rounded px-3 py-1 border-neutral-600 bg-neutral-700 cursor-pointer select-none"
          >
            <span className="flex items-center" onClick={scrollDomToBottom}>
              <VscArrowDown className="inline mr-2 w-3 h-3" />
              <span className="inline-block" onClick={scrollDomToBottom}>
                {t(I18nKey.CHAT_INTERFACE$TO_BOTTOM)}
              </span>
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

export default Jupyter;
