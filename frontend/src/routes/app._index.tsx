import React from "react";
import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { Editor, Monaco } from "@monaco-editor/react";
import { type editor } from "monaco-editor";
import { VscCode } from "react-icons/vsc";
import {
  ClientActionFunctionArgs,
  json,
  useFetcher,
  useLoaderData,
  useRouteError,
} from "@remix-run/react";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { I18nKey } from "#/i18n/declaration";
import FileExplorer from "#/components/file-explorer/FileExplorer";
import {
  retrieveFiles,
  retrieveFileContent,
  saveFileContent,
} from "#/api/open-hands";
import { setChanged } from "#/state/file-state-slice";
import { clientAction as saveFileContentClientAction } from "#/routes/save-file-content";
import { useSocket } from "#/context/socket";
import { FilesProvider, useFiles } from "#/context/files";

interface CodeEditorCompoonentProps {
  isReadOnly: boolean;
}

function CodeEditorCompoonent({ isReadOnly }: CodeEditorCompoonentProps) {
  const {
    files,
    selectedPath,
    modifiedFiles,
    modifyFileContent,
    saveFileContent: saveNewFileContent,
  } = useFiles();

  const handleEditorDidMount = React.useCallback(
    (editor: editor.IStandaloneCodeEditor, monaco: Monaco): void => {
      monaco.editor.defineTheme("my-theme", {
        base: "vs-dark",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": "#171717",
        },
      });

      monaco.editor.setTheme("my-theme");
    },
    [],
  );

  const handleEditorChange = (value: string | undefined) => {
    if (selectedPath && value) modifyFileContent(selectedPath, value);
  };

  React.useEffect(() => {
    const handleSave = async (event: KeyboardEvent) => {
      if (selectedPath && event.metaKey && event.key === "s") {
        event.preventDefault();
        const content = saveNewFileContent(selectedPath);

        if (content) {
          try {
            const token = localStorage.getItem("token")?.toString();
            if (token) await saveFileContent(token, selectedPath, content);
          } catch (error) {
            // handle error
          }
        }
      }
    };

    document.addEventListener("keydown", handleSave);
    return () => {
      document.removeEventListener("keydown", handleSave);
    };
  }, []);

  return (
    <Editor
      data-testid="code-editor"
      height="100%"
      path={selectedPath ?? undefined}
      defaultValue=""
      value={
        selectedPath
          ? modifiedFiles[selectedPath] || files[selectedPath]
          : undefined
      }
      onMount={handleEditorDidMount}
      onChange={handleEditorChange}
      options={{ readOnly: isReadOnly }}
    />
  );
}

export const clientLoader = async () => {
  const token = localStorage.getItem("token");
  return json({ token });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const token = localStorage.getItem("token");

  const formData = await request.formData();
  const file = formData.get("file")?.toString();

  let selectedFileContent: string | null = null;

  if (file && token) {
    selectedFileContent = await retrieveFileContent(token, file);
  }

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
  const { token } = useLoaderData<typeof clientLoader>();
  const fetcher = useFetcher<typeof clientAction>({ key: "file-selector" });
  const saveFile = useFetcher<typeof saveFileContentClientAction>({
    key: "save-file",
  });
  const [fileContents, setFileContents] = React.useState<
    Record<string, string>
  >({});

  const { runtimeActive } = useSocket();
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const activeFilepath = useSelector((state: RootState) => state.code.path);
  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  const [files, setFiles] = React.useState<string[]>([]);

  React.useEffect(() => {
    // only retrieve files if connected to WS to prevent requesting before runtime is ready
    if (runtimeActive && token) retrieveFiles(token).then(setFiles);
  }, [runtimeActive, token]);

  React.useEffect(() => {
    if (saveFile.data?.success) {
      // refetch file content
      const refetchFileFormData = new FormData();
      refetchFileFormData.append("file", activeFilepath);
      fetcher.submit(refetchFileFormData, {
        method: "POST",
      });

      // if save file is successful, mark the file as unchanged
      dispatch(
        setChanged({
          path: activeFilepath,
          changed: false,
        }),
      );
    } else {
      // TODO: handle error
    }
  }, [saveFile.data]);

  React.useEffect(() => {
    if (fetcher.data?.selectedFileContent) {
      setFileContents((prev) => ({
        ...prev,
        [activeFilepath]: fetcher.data!.selectedFileContent || "",
      }));
    }
  }, [fetcher.data]);

  const isEditingAllowed = React.useMemo(
    () =>
      agentState === AgentState.INIT ||
      agentState === AgentState.PAUSED ||
      agentState === AgentState.FINISHED ||
      agentState === AgentState.AWAITING_USER_INPUT,
    [agentState],
  );

  return (
    <FilesProvider defaultPaths={files}>
      <div className="flex h-full w-full bg-neutral-900 relative">
        <FileExplorer />
        <div className="flex flex-col min-h-0 w-full pt-3">
          <div className="flex grow items-center justify-center">
            {!fileContents[activeFilepath] &&
            !fetcher.data?.selectedFileContent ? (
              <div
                data-testid="code-editor-empty-message"
                className="flex flex-col items-center text-neutral-400"
              >
                <VscCode size={100} />
                {t(I18nKey.CODE_EDITOR$EMPTY_MESSAGE)}
              </div>
            ) : (
              <CodeEditorCompoonent isReadOnly={!isEditingAllowed} />
            )}
          </div>
        </div>
      </div>
    </FilesProvider>
  );
}

export default CodeEditor;
