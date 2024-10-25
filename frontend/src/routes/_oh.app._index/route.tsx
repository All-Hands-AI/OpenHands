import React from "react";
import { useSelector } from "react-redux";
import { json, useLoaderData, useRouteError } from "@remix-run/react";
import toast from "react-hot-toast";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import FileExplorer from "#/components/file-explorer/FileExplorer";
import OpenHands from "#/api/open-hands";
import { useSocket } from "#/context/socket";
import CodeEditorCompoonent from "./code-editor-component";
import { useFiles } from "#/context/files";
import { EditorActions } from "#/components/editor-actions";

export const clientLoader = async () => {
  const token = localStorage.getItem("token");
  return json({ token });
};

export function ErrorBoundary() {
  const error = useRouteError();

  return (
    <div className="w-full h-full border border-danger rounded-b-xl flex flex-col items-center justify-center gap-2 bg-red-500/5">
      <h1 className="text-3xl font-bold">Oops! An error occurred!</h1>
      {error instanceof Error && <pre>{error.message}</pre>}
    </div>
  );
}

function CodeEditor() {
  const { token } = useLoaderData<typeof clientLoader>();
  const { runtimeActive } = useSocket();
  const {
    setPaths,
    selectedPath,
    modifiedFiles,
    saveFileContent: saveNewFileContent,
    discardChanges,
  } = useFiles();

  const [errors, setErrors] = React.useState<{ getFiles: string | null }>({
    getFiles: null,
  });

  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  React.useEffect(() => {
    // only retrieve files if connected to WS to prevent requesting before runtime is ready
    if (runtimeActive && token) {
      OpenHands.getFiles(token)
        .then(setPaths)
        .catch(() => {
          setErrors({ getFiles: "Failed to retrieve files" });
        });
    }
  }, [runtimeActive, token]);

  // Code editing is only allowed when the agent is paused, finished, or awaiting user input (server rules)
  const isEditingAllowed = React.useMemo(
    () =>
      agentState === AgentState.PAUSED ||
      agentState === AgentState.FINISHED ||
      agentState === AgentState.AWAITING_USER_INPUT,
    [agentState],
  );

  const handleSave = async () => {
    if (selectedPath) {
      const content = modifiedFiles[selectedPath];
      if (content && token) {
        try {
          await OpenHands.saveFile(token, selectedPath, content);
          saveNewFileContent(selectedPath);
        } catch (error) {
          toast.error("Failed to save file");
        }
      }
    }
  };

  const handleDiscard = () => {
    if (selectedPath) discardChanges(selectedPath);
  };

  return (
    <div className="flex h-full w-full bg-neutral-900 relative">
      <FileExplorer error={errors.getFiles} />
      <div className="flex flex-col min-h-0 w-full">
        {selectedPath && (
          <div className="flex w-full items-center justify-between self-end p-2">
            <span className="text-sm text-neutral-500">{selectedPath}</span>
            <EditorActions
              onSave={handleSave}
              onDiscard={handleDiscard}
              isDisabled={!isEditingAllowed || !modifiedFiles[selectedPath]}
            />
          </div>
        )}
        <div className="flex grow items-center justify-center">
          <CodeEditorCompoonent isReadOnly={!isEditingAllowed} />
        </div>
      </div>
    </div>
  );
}

export default CodeEditor;
