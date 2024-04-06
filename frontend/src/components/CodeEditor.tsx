import Editor, { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import React, { useState } from "react";
import { Tabs, Tab } from "@nextui-org/react";
import { useSelector } from "react-redux";
import { RootState } from "../store";
import Files from "./Files";
import { cn } from "../utils/utils";

function CodeEditor(): JSX.Element {
  const [selectedFileName, setSelectedFileName] = useState("welcome");
  const [explorerOpen, setExplorerOpen] = useState(true);
  const code = useSelector((state: RootState) => state.code.code);

  const bgColor = getComputedStyle(document.documentElement)
    .getPropertyValue("--bg-workspace")
    .trim();

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
        "editor.background": bgColor,
      },
    });

    // 应用自定义主题 - English: apply custom theme
    monaco.editor.setTheme("my-theme");
  };

  return (
    <div
      className={`${cn(
        explorerOpen ? "grid-cols-[250px_auto]" : "grid-cols-[50px_auto]",
      )} grid h-full bg-bg-workspace transition-all duration-500 ease-in-out`}
    >
      <div>
        <Files
          setSelectedFileName={setSelectedFileName}
          setExplorerOpen={setExplorerOpen}
          explorerOpen={explorerOpen}
        />
      </div>
      <div>
        <Tabs
          disableCursorAnimation
          classNames={{
            tabList:
              "gap-6 w-full relative rounded-none bg-bg-workspace p-0 border-b border-r border-divider ",
            cursor: "w-full bg-bg-workspace rounded-none",
            tab: "max-w-fit px-4 h-12",
            tabContent: "group-data-[selected=true]:text-text-editor-active",
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
          >
            <div>
              <Editor
                height="100vh"
                theme="vs-dark"
                defaultLanguage="python"
                defaultValue="# Welcome to OpenDevin!"
                value={code}
                onMount={handleEditorDidMount}
              />
            </div>
          </Tab>
        </Tabs>
      </div>
    </div>
  );
}

export default CodeEditor;
