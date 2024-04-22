import Editor, { Monaco } from "@monaco-editor/react";
import { Tab, Tabs } from "@nextui-org/react";
import type { editor } from "monaco-editor";
import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "#/store";
import { selectFile } from "#/services/fileService";
import { setCode } from "#/state/codeSlice";
import FileExplorer from "./file-explorer/FileExplorer";

function CodeEditor(): JSX.Element {
  const [selectedFileName, setSelectedFileName] = useState("welcome");

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
    const fileName = paths[paths.length - 1];
    const rootlessPath = paths.slice(1).join("/");

    setSelectedFileName(fileName);

    const newCode = await selectFile(rootlessPath);
    dispatch(setCode(newCode));
  };

  return (
    <div className="flex h-full w-full bg-neutral-900 transition-all duration-500 ease-in-out">
      <FileExplorer onFileClick={onSelectFile} />
      <div className="flex flex-col min-h-0 w-full">
        <Tabs
          disableCursorAnimation
          classNames={{
            base: "border-b border-divider",
            tabList:
              "w-full relative rounded-none bg-neutral-900 p-0 border-divider",
            cursor: "w-full bg-neutral-600 rounded-none",
            tab: "max-w-fit px-4 h-[36px]",
            tabContent: "group-data-[selected=true]:text-white ",
          }}
          aria-label="Options"
        >
          <Tab
            key={
              selectedFileName === ""
                ? "Welcome"
                : selectedFileName.toLocaleLowerCase()
            }
            title={!selectedFileName ? "Welcome" : selectedFileName}
          />
        </Tabs>
        <div className="flex grow">
          <Editor
            height="100%"
            path={
              selectedFileName === ""
                ? "welcome.txt"
                : selectedFileName.toLocaleLowerCase()
            }
            defaultValue="# Welcome to OpenDevin!"
            value={code}
            onMount={handleEditorDidMount}
          />
        </div>
      </div>
    </div>
  );
}

export default CodeEditor;
