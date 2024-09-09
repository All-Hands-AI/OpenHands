import React, { Suspense } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { Editor, Monaco } from "@monaco-editor/react";
import { type editor } from "monaco-editor";
import { VscCheck, VscClose, VscCode, VscSave } from "react-icons/vsc";
import { Button, Tab, Tabs } from "@nextui-org/react";
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
import {
  addOrUpdateFileState,
  FileState,
  setCode,
  setFileStates,
} from "#/state/codeSlice";
import { saveFile } from "#/services/fileService";
import toast from "#/utils/toast";
import { I18nKey } from "#/i18n/declaration";
import FileExplorer from "#/components/file-explorer/FileExplorer";
import { retrieveFiles, retrieveFileContent } from "#/api/open-hands";

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

  throw new Error("Unauthorized");
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const file = formData.get("file")?.toString();

  let selectedFileContent: string | null = null;

  if (file) {
    selectedFileContent = await retrieveFileContent(file);
  }

  return json({ selectedFileContent });
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

  const { t } = useTranslation();
  const dispatch = useDispatch();
  const fileStates = useSelector((state: RootState) => state.code.fileStates);
  const activeFilepath = useSelector((state: RootState) => state.code.path);
  const fileState = fileStates.find((f) => f.path === activeFilepath);
  const agentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );
  const [saveStatus, setSaveStatus] = React.useState<
    "idle" | "saving" | "saved" | "error"
  >("idle");
  const [showSaveNotification, setShowSaveNotification] = React.useState(false);
  const unsavedContent = fileState?.unsavedContent;
  const hasUnsavedChanges = fileState?.savedContent !== unsavedContent;

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

  React.useEffect(() => {
    setSaveStatus("idle");
    // Clear out any file states where the file is not being viewed and does not have any changes
    const newFileStates = fileStates.filter(
      (f) => f.path === activeFilepath || f.savedContent !== f.unsavedContent,
    );
    if (fileStates.length !== newFileStates.length) {
      dispatch(setFileStates(newFileStates));
    }
  }, [activeFilepath]);

  React.useEffect(() => {
    if (!showSaveNotification) {
      return undefined;
    }
    const timeout = setTimeout(() => setShowSaveNotification(false), 2000);
    return () => clearTimeout(timeout);
  }, [showSaveNotification]);

  const handleEditorChange = React.useCallback(
    (value: string | undefined): void => {
      if (value !== undefined && isEditingAllowed) {
        dispatch(setCode(value));
        const newFileState = {
          path: activeFilepath,
          savedContent: fileState?.savedContent,
          unsavedContent: value,
        };
        dispatch(addOrUpdateFileState(newFileState));
      }
    },
    [activeFilepath, dispatch, isEditingAllowed],
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

  const handleSave = React.useCallback(async (): Promise<void> => {
    if (saveStatus === "saving" || !isEditingAllowed) return;

    setSaveStatus("saving");

    try {
      const newContent = fileState?.unsavedContent;
      if (newContent) {
        await saveFile(activeFilepath, newContent);
      }
      setSaveStatus("saved");
      setShowSaveNotification(true);
      const newFileState = {
        path: activeFilepath,
        savedContent: newContent,
        unsavedContent: newContent,
      };
      dispatch(addOrUpdateFileState(newFileState));
      toast.success(
        "file-save-success",
        t(I18nKey.CODE_EDITOR$FILE_SAVED_SUCCESSFULLY),
      );
    } catch (error) {
      setSaveStatus("error");
      if (error instanceof Error) {
        toast.error(
          "file-save-error",
          `${t(I18nKey.CODE_EDITOR$FILE_SAVE_ERROR)}: ${error.message}`,
        );
      } else {
        toast.error("file-save-error", t(I18nKey.CODE_EDITOR$FILE_SAVE_ERROR));
      }
    }
  }, [saveStatus, activeFilepath, unsavedContent, isEditingAllowed, t]);

  const handleCancel = React.useCallback(() => {
    const { path, savedContent } = fileState as FileState;
    dispatch(
      addOrUpdateFileState({
        path,
        savedContent,
        unsavedContent: savedContent,
      }),
    );
  }, [activeFilepath, unsavedContent]);

  const getSaveButtonColor = () => {
    switch (saveStatus) {
      case "saving":
        return "bg-yellow-600";
      case "saved":
        return "bg-green-600";
      case "error":
        return "bg-red-600";
      default:
        return "bg-blue-600";
    }
  };

  return (
    <div className="flex h-full w-full bg-neutral-900 relative">
      <Suspense fallback={<FileExplorerFallback />}>
        <Await resolve={files}>
          {(resolvedFiled) => <FileExplorer files={resolvedFiled} />}
        </Await>
      </Suspense>
      <div className="flex flex-col min-h-0 w-full">
        <div className="flex justify-between items-center border-b border-neutral-600 mb-4">
          <Tabs
            disableCursorAnimation
            classNames={{
              base: "w-full",
              tabList:
                "w-full relative rounded-none bg-neutral-900 p-0 border-divider",
              cursor: "w-full bg-neutral-600 rounded-none",
              tab: "max-w-fit px-4 h-[36px]",
              tabContent: "group-data-[selected=true]:text-white",
            }}
            aria-label={t(I18nKey.CODE_EDITOR$OPTIONS)}
          >
            <Tab
              key={selectedFileName}
              title={selectedFileName || t(I18nKey.CODE_EDITOR$EMPTY_MESSAGE)}
            />
          </Tabs>
          {selectedFileName && hasUnsavedChanges && (
            <div className="flex items-center mr-2">
              <Button
                onClick={handleCancel}
                className="text-white transition-colors duration-300 mr-2"
                size="sm"
                startContent={<VscClose />}
              >
                {t(I18nKey.FEEDBACK$CANCEL_LABEL)}
              </Button>
              <Button
                onClick={handleSave}
                className={`${getSaveButtonColor()} text-white transition-colors duration-300 mr-2`}
                size="sm"
                startContent={<VscSave />}
                disabled={saveStatus === "saving" || !isEditingAllowed}
              >
                {saveStatus === "saving"
                  ? t(I18nKey.CODE_EDITOR$SAVING_LABEL)
                  : t(I18nKey.CODE_EDITOR$SAVE_LABEL)}
              </Button>
            </div>
          )}
        </div>
        <div className="flex grow items-center justify-center">
          {!fetcher.data?.selectedFileContent ? (
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
              value={fetcher.data.selectedFileContent}
              onMount={handleEditorDidMount}
              onChange={handleEditorChange}
              options={{ readOnly: !isEditingAllowed }}
            />
          )}
        </div>
      </div>
      {showSaveNotification && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <div className="bg-green-500 text-white px-4 py-2 rounded-lg flex items-center justify-center animate-pulse">
            <VscCheck className="mr-2 text-xl" />
            <span>{t(I18nKey.CODE_EDITOR$FILE_SAVED_SUCCESSFULLY)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default CodeEditor;
