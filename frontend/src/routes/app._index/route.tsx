import React from "react";
import { useSelector } from "react-redux";
import {
  ClientActionFunctionArgs,
  json,
  useRouteError,
} from "@remix-run/react";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import FileExplorer from "#/components/file-explorer/FileExplorer";
import OpenHands from "#/api/open-hands";
import { useSocket } from "#/context/socket";
import CodeEditorCompoonent from "./code-editor-component";
import { useFiles } from "#/context/files";

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const file = formData.get("file")?.toString();

  let selectedFileContent: string | null = null;
  if (file) selectedFileContent = await OpenHands.getFile(file);

  return json({ file, selectedFileContent });
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
  const { runtimeActive } = useSocket();
  const { setPaths } = useFiles();

  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  React.useEffect(() => {
    // only retrieve files if connected to WS to prevent requesting before runtime is ready
    if (runtimeActive) OpenHands.getFiles().then(setPaths);
  }, [runtimeActive]);

  // Code editing is only allowed when the agent is paused, finished, or awaiting user input (server rules)
  const isEditingAllowed = React.useMemo(
    () =>
      agentState === AgentState.PAUSED ||
      agentState === AgentState.FINISHED ||
      agentState === AgentState.AWAITING_USER_INPUT,
    [agentState],
  );

  return (
    <div className="flex h-full w-full bg-neutral-900 relative">
      <FileExplorer />
      <div className="flex flex-col min-h-0 w-full pt-3">
        <div className="flex grow items-center justify-center">
          <CodeEditorCompoonent isReadOnly={!isEditingAllowed} />
        </div>
      </div>
    </div>
  );
}

export default CodeEditor;
