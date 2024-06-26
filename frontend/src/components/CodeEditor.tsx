import React, { useMemo, useState, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import Editor, { Monaco } from "@monaco-editor/react";
import { Tab, Tabs, Button } from "@nextui-org/react";
import { VscCode, VscSave, VscCheck } from "react-icons/vsc";
import type { editor } from "monaco-editor";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import FileExplorer from "./file-explorer/FileExplorer";
import { setCode } from "#/state/codeSlice";
import toast from "#/utils/toast";
import { saveFile } from "#/services/fileService";
import AgentState from "#/types/AgentState";

function CodeEditor(): JSX.Element {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const code = useSelector((state: RootState) => state.code.code);
  const activeFilepath = useSelector((state: RootState) => state.code.path);
  const agentState = useSelector((state: RootState) => state.agent.curAgentState);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [showSaveNotification, setShowSaveNotification] = useState(false);

  const selectedFileName = useMemo(() => {
    const paths = activeFilepath.split("/");
    return paths[paths.length - 1];
  }, [activeFilepath]);

  const isEditingAllowed = useMemo(() => {
    return agentState === AgentState.PAUSED || agentState === AgentState.FINISHED;
  }, [agentState]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (saveStatus === 'saved') {
      timer = setTimeout(() => setSaveStatus('idle'), 3000);
    }
    return () => clearTimeout(timer);
  }, [saveStatus]);

  const handleEditorDidMount = useCallback((
    editor: editor.IStandaloneCodeEditor,
    monaco: Monaco
  ): void => {
    monaco.editor.defineTheme("my-theme", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#171717",
      },
    });

    monaco.editor.setTheme("my-theme");
  }, []);

  const handleEditorChange = useCallback((value: string | undefined): void => {
    if (value !== undefined && isEditingAllowed) {
      dispatch(setCode(value));
      setSaveStatus('idle');
    }
  }, [dispatch, isEditingAllowed]);

  const handleSave = useCallback(async (): Promise<void> => {
    if (saveStatus === 'saving' || !isEditingAllowed) return;

    setSaveStatus('saving');
    setLastSaved(null);

    try {
      await saveFile(activeFilepath, code);
      const now = new Date().toLocaleTimeString();
      setLastSaved(now);
      setSaveStatus('saved');
      setShowSaveNotification(true);
      setTimeout(() => setShowSaveNotification(false), 2000);
      toast.success("File saved successfully!", "Save Successful");
      console.log(`File "${selectedFileName}" has been saved.`);
    } catch (error) {
      console.error("Error saving file:", error);
      setSaveStatus('error');
      if (error instanceof Error) {
        toast.error(`Failed to save file: ${error.message}`, "Save Error");
      } else {
        toast.error("An unknown error occurred while saving the file", "Save Error");
      }
    }
  }, [saveStatus, activeFilepath, code, selectedFileName, isEditingAllowed]);

  const getSaveButtonColor = () => {
    switch (saveStatus) {
      case 'saving': return 'bg-yellow-600';
      case 'saved': return 'bg-green-600';
      case 'error': return 'bg-red-600';
      default: return 'bg-blue-600';
    }
  };

  return (
    <div className="flex h-full w-full bg-neutral-900 transition-all duration-500 ease-in-out relative">
      <FileExplorer />
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
            aria-label="Options"
          >
            <Tab
              key={selectedFileName.toLowerCase()}
              title={selectedFileName || "No file selected"}
            />
          </Tabs>
          {selectedFileName && (
            <div className="flex items-center mr-2">
              <Button
                onClick={handleSave}
                className={`${getSaveButtonColor()} text-white transition-colors duration-300 mr-2`}
                size="sm"
                startContent={<VscSave />}
                disabled={saveStatus === 'saving' || !isEditingAllowed}
              >
                {saveStatus === 'saving' ? "Saving..." : "Save"}
              </Button>
              {lastSaved && (
                <span className="text-xs text-gray-400">
                  Last saved: {lastSaved}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex grow items-center justify-center">
          {!selectedFileName ? (
            <div className="flex flex-col items-center text-neutral-400">
              <VscCode size={100} />
              {t(I18nKey.CODE_EDITOR$EMPTY_MESSAGE)}
            </div>
          ) : (
            <Editor
              height="100%"
              path={selectedFileName.toLowerCase()}
              defaultValue=""
              value={code}
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
            <span>File saved successfully</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default CodeEditor;