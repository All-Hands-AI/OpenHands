import React from "react";
import { useSelector } from "react-redux";
import { useRouteError } from "react-router";
import { editor } from "monaco-editor";
import { EditorProps } from "@monaco-editor/react";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import CodeEditorComponent from "../../components/features/editor/code-editor-component";
import { useFiles } from "#/context/files";
import { useSaveFile } from "#/hooks/mutation/use-save-file";
import { ASSET_FILE_TYPES } from "./constants";
import { EditorActions } from "#/components/features/editor/editor-actions";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";

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
  const {
    selectedPath,
    modifiedFiles,
    saveFileContent: saveNewFileContent,
    discardChanges,
  } = useFiles();

  const [fileExplorerIsOpen, setFileExplorerIsOpen] = React.useState(true);
  const editorRef = React.useRef<editor.IStandaloneCodeEditor | null>(null);

  const { mutate: saveFile } = useSaveFile();

  const toggleFileExplorer = () => {
    setFileExplorerIsOpen((prev) => !prev);
    editorRef.current?.layout({ width: 0, height: 0 });
  };

  const handleEditorDidMount: EditorProps["onMount"] = (e, monaco) => {
    editorRef.current = e;

    monaco.editor.defineTheme("oh-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#171717",
      },
    });
    monaco.editor.setTheme("oh-dark");
  };

  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

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
      if (content) {
        saveFile({ path: selectedPath, content });
        saveNewFileContent(selectedPath);
      }
    }
  };

  const handleDiscard = () => {
    if (selectedPath) discardChanges(selectedPath);
  };

  const isAssetFileType = selectedPath
    ? ASSET_FILE_TYPES.some((ext) => selectedPath.endsWith(ext))
    : false;

  return (
    <div className="flex h-full bg-neutral-900 relative">
      <FileExplorer isOpen={fileExplorerIsOpen} onToggle={toggleFileExplorer} />
      <div className="w-full">
        {selectedPath && !isAssetFileType && (
          <div className="flex w-full items-center justify-between self-end p-2">
            <span className="text-sm text-neutral-500">{selectedPath}</span>
            <EditorActions
              onSave={handleSave}
              onDiscard={handleDiscard}
              isDisabled={!isEditingAllowed || !modifiedFiles[selectedPath]}
            />
          </div>
        )}
        <CodeEditorComponent
          onMount={handleEditorDidMount}
          isReadOnly={!isEditingAllowed}
        />
      </div>
    </div>
  );
}

export default CodeEditor;
