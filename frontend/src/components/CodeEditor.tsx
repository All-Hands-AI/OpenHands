import React from "react";
import Editor from "@monaco-editor/react";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function CodeEditor(): JSX.Element {
  const code = useSelector((state: RootState) => state.code.code);

  return (
    <Editor
      height="100%"
      theme="vs-dark"
      defaultLanguage="python"
      defaultValue="# Welcome to OpenDevin!"
      value={code}
    />
  );
}

export default CodeEditor;
