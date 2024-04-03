import React from "react";
import Editor, { Monaco } from "@monaco-editor/react";
import { useSelector } from "react-redux";
import type { editor } from "monaco-editor";
import { RootState } from "../store";

function CodeEditor(): JSX.Element {
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
    <div className="w-full h-full bg-bg-workspace">
      <Editor
        height="95%"
        theme="vs-dark"
        defaultLanguage="python"
        defaultValue="# Welcome to OpenDevin!"
        value={code}
        onMount={handleEditorDidMount}
      />
    </div>
  );
}

export default CodeEditor;
