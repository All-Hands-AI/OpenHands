import { useQueryClient } from "@tanstack/react-query";
import React from "react";

const JUPYTER_KEY = ["_STATE", "jupyter"];

interface JupyterCell {
  type: "input" | "output";
  content: string;
}

export const useJupyter = () => {
  const queryClient = useQueryClient();

  const addCell = React.useCallback(
    (cell: JupyterCell) => {
      queryClient.setQueryData<JupyterCell[]>(JUPYTER_KEY, (old) =>
        old ? [...old, cell] : [cell],
      );
    },
    [queryClient],
  );

  const addInputCell = React.useCallback(
    (code: string) => {
      addCell({ type: "input", content: code });
    },
    [addCell],
  );

  const addOutputCell = React.useCallback(
    (content: string) => {
      addCell({ type: "output", content });
    },
    [addCell],
  );

  const clearCells = React.useCallback(() => {
    queryClient.setQueryData<JupyterCell[]>(JUPYTER_KEY, []);
  }, [queryClient]);

  const cells = queryClient.getQueryData<JupyterCell[]>(JUPYTER_KEY) || [];

  return { cells, addInputCell, addOutputCell, clearCells };
};
