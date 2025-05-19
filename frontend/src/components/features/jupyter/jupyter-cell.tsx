import React from "react";
import { Cell } from "#/state/jupyter-slice";
import { JupyterLine, parseCellContent } from "#/utils/parse-cell-content";
import { JupytrerCellInput } from "./jupyter-cell-input";
import { JupyterCellOutput } from "./jupyter-cell-output";

interface JupyterCellProps {
  cell: Cell;
}

export function JupyterCell({ cell }: JupyterCellProps) {
  const [lines, setLines] = React.useState<JupyterLine[]>([]);

  React.useEffect(() => {
    setLines(parseCellContent(cell.content, cell.imageUrls));
  }, [cell.content, cell.imageUrls]);

  if (cell.type === "input") {
    return <JupytrerCellInput code={cell.content} />;
  }

  return <JupyterCellOutput lines={lines} />;
}
