import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";

interface JupytrerCellInputProps {
  code: string;
}

export function JupytrerCellInput({ code }: JupytrerCellInputProps) {
  return (
    <div className="rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs">
      <div className="mb-1 text-gray-400">EXECUTE</div>
      <pre
        className="scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5"
        style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
      >
        <SyntaxHighlighter language="python" style={atomOneDark} wrapLongLines>
          {code}
        </SyntaxHighlighter>
      </pre>
    </div>
  );
}
