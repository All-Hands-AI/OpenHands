import React, { Suspense } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { Editor, Monaco } from "@monaco-editor/react";
import { type editor } from "monaco-editor";
import { VscCode } from "react-icons/vsc";
import {
  Await,
  ClientActionFunctionArgs,
  defer,
  json,
  useFetcher,
  useLoaderData,
  useRouteError,
} from "@remix-run/react";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";
import { I18nKey } from "#/i18n/declaration";
import FileExplorer from "#/components/file-explorer/FileExplorer";
import { retrieveFiles, retrieveFileContent } from "#/api/open-hands";
import { setChanged } from "#/state/file-state-slice";
import { clientAction as saveFileContentClientAction } from "#/routes/save-file-content";

function FileExplorerFallback() {
  return (
    <div className="h-full w-60 border border-yellow-500 rounded-bl-xl bg-neutral-800 px-3 py-2">
      Loading files...
    </div>
  );
}

export const clientLoader = async () => {
  const token = localStorage.getItem("token");

  if (token) {
    const files = retrieveFiles(token);
    return defer({ files });
  }

  return defer({ files: Promise.resolve([]) }, { status: 401 });
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
  const { files } = useLoaderData<typeof clientLoader>();
  const fetcher = useFetcher<typeof clientAction>({ key: "file-selector" });
  const saveFile = useFetcher<typeof saveFileContentClientAction>({
    key: "save-file",
  });
  const [fileContents, setFileContents] = React.useState<
    Record<string, string>
  >({});

  const { t } = useTranslation();
  const dispatch = useDispatch();
  const activeFilepath = useSelector((state: RootState) => state.code.path);
  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  React.useEffect(() => {
    // save file content on cmd+s
    const handleSave = (event: KeyboardEvent) => {
      if (event.metaKey && event.key === "s") {
        event.preventDefault();

        if (fileContents[activeFilepath]) {
          const saveFileFormData = new FormData();
          saveFileFormData.append("file", activeFilepath);
          saveFileFormData.append(
            "content",
            fileContents[activeFilepath].trimEnd() || "",
          );
          saveFile.submit(saveFileFormData, {
            method: "POST",
            action: "/save-file-content",
          });
        }
      }
    };

    document.addEventListener("keydown", handleSave);

    return () => {
      document.removeEventListener("keydown", handleSave);
    };
  }, [activeFilepath, fileContents, fetcher]);

  React.useEffect(() => {
    // if save file is successful, mark the file as unchanged
    if (saveFile.data?.success) {
      // refetch file content
      const refetchFileFormData = new FormData();
      refetchFileFormData.append("file", activeFilepath);
      fetcher.submit(refetchFileFormData, {
        method: "POST",
      });

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

  const selectedFileName = React.useMemo(() => {
    const paths = activeFilepath.split("/");
    return paths[paths.length - 1];
  }, [activeFilepath]);

  const isEditingAllowed = React.useMemo(
    () =>
      agentState === AgentState.INIT ||
      agentState === AgentState.PAUSED ||
      agentState === AgentState.FINISHED ||
      agentState === AgentState.AWAITING_USER_INPUT,
    [agentState],
  );

  const handleEditorChange = React.useCallback(
    (value: string | undefined): void => {
      if (value && isEditingAllowed) {
        setFileContents((prev) => ({ ...prev, [activeFilepath]: value }));
        dispatch(
          setChanged({
            path: activeFilepath,
            changed: value !== fetcher.data?.selectedFileContent,
          }),
        );
      }
    },
    [
      dispatch,
      activeFilepath,
      isEditingAllowed,
      fetcher.data?.selectedFileContent,
    ],
  );

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

  return (
    <div className="flex h-full w-full bg-neutral-900 relative">
      <Suspense fallback={<FileExplorerFallback />}>
        <Await resolve={files}>
          {(resolvedFiled) => <FileExplorer files={resolvedFiled} />}
        </Await>
      </Suspense>
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
            <Editor
              data-testid="code-editor"
              height="100%"
              path={selectedFileName.toLowerCase()}
              defaultValue=""
              value={
                fileContents[activeFilepath] ||
                fetcher.data?.selectedFileContent ||
                ""
              }
              onMount={handleEditorDidMount}
              onChange={handleEditorChange}
              options={{ readOnly: !isEditingAllowed }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default CodeEditor;
