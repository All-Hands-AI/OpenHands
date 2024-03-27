import React from "react";
import Editor from "@monaco-editor/react";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function CodeEditor(): JSX.Element {
  const code = useSelector((state: RootState) => state.code.code);

  return (
    <div
      className="editor"
      style={{
        height: "100%",
        margin: "1rem",
        borderRadius: "1rem",
      }}
    >
      <Editor
        height="95%"
        theme="vs-dark"
        defaultLanguage="python"
        defaultValue="# Welcome to OpenDevin!"
        value={code}
      />
    </div>
  );
}

export default CodeEditor;
