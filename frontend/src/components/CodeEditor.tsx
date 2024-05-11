import Editor, { Monaco } from "@monaco-editor/react";
import { Tab, Tabs } from "@nextui-org/react";
import type { editor } from "monaco-editor";
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
import { useDispatch, useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { selectFile } from "#/services/fileService";
import { setCode } from "#/state/codeSlice";
import { RootState } from "#/store";
import FileExplorer from "./file-explorer/FileExplorer";
import { CodeEditorContext } from "./CodeEditorContext";

function CodeEditor(): JSX.Element {
  const { t } = useTranslation();
  const [selectedFileAbsolutePath, setSelectedFileAbsolutePath] = useState("");
  const selectedFileName = useMemo(() => {
    const paths = selectedFileAbsolutePath.split("/");
    return paths[paths.length - 1];
  }, [selectedFileAbsolutePath]);
  const codeEditorContext = useMemo(
    () => ({ selectedFileAbsolutePath }),
    [selectedFileAbsolutePath],
  );

  const dispatch = useDispatch();
  const code = useSelector((state: RootState) => state.code.code);

  const handleEditorDidMount = (
    editor: editor.IStandaloneCodeEditor,
    monaco: Monaco,
  ) => {
    // 定义一个自定义主题 - English: Define a custom theme
    monaco.editor.defineTheme("my-theme", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#171717",
      },
    });

    // 应用自定义主题 - English: apply custom theme
    monaco.editor.setTheme("my-theme");
  };

  const onSelectFile = async (absolutePath: string) => {
    const paths = absolutePath.split("/");
    const rootlessPath = paths.slice(1).join("/");

    setSelectedFileAbsolutePath(absolutePath);

    const newCode = await selectFile(rootlessPath);
    dispatch(setCode(newCode));
  };

  return (
    <div className="flex h-full w-full bg-neutral-900 transition-all duration-500 ease-in-out">
      <CodeEditorContext.Provider value={codeEditorContext}>
        <FileExplorer onFileClick={onSelectFile} />
        <div className="flex flex-col min-h-0 w-full">
          <Tabs
            disableCursorAnimation
            classNames={{
              base: "border-b border-divider border-neutral-600 mb-4",
              tabList:
                "w-full relative rounded-none bg-neutral-900 p-0 border-divider",
              cursor: "w-full bg-neutral-600 rounded-none",
              tab: "max-w-fit px-4 h-[36px]",
              tabContent: "group-data-[selected=true]:text-white",
            }}
            aria-label="Options"
          >
            <Tab
              key={selectedFileName.toLocaleLowerCase()}
              title={selectedFileName}
            />
          </Tabs>
          <div className="flex grow items-center justify-center">
            {selectedFileName === "" ? (
              <div className="flex flex-col items-center text-neutral-400">
                <VscCode size={100} />
                {t(I18nKey.CODE_EDITOR$EMPTY_MESSAGE)}
              </div>
            ) : (
              <Editor
                height="100%"
                path={selectedFileName.toLocaleLowerCase()}
                defaultValue=""
                value={code}
                onMount={handleEditorDidMount}
              />
            )}
          </div>
        </div>
      </CodeEditorContext.Provider>
    </div>
  );
}

export default CodeEditor;
