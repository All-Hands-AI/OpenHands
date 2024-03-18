import React from "react";
import Editor from "@monaco-editor/react";

function CodeEditor(): JSX.Element {
  const handleEditorChange = (value: string | undefined) => {
    console.log("Content changed:", value);
  };

  return (
    <Editor
      height="100%"
      defaultLanguage="javascript"
      defaultValue="// Welcome to OpenDevin!"
      onChange={handleEditorChange}
    />
  );
}

export default CodeEditor;
