import { Editor, Monaco, EditorProps } from "@monaco-editor/react";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
import { type editor } from "monaco-editor";
import toast from "react-hot-toast";
import { I18nKey } from "#/i18n/declaration";
import { useFiles } from "#/context/files";
import OpenHands from "#/api/open-hands";

interface CodeEditorCompoonentProps {
  onMount: EditorProps["onMount"];
  isReadOnly: boolean;
}

function CodeEditorCompoonent({
  onMount,
  isReadOnly,
}: CodeEditorCompoonentProps) {
  const { t } = useTranslation();
  const {
    files,
    selectedPath,
    modifiedFiles,
    modifyFileContent,
    saveFileContent: saveNewFileContent,
  } = useFiles();

  const [cursorPosition, setCursorPosition] = useState({ line: 1, column: 1 });

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

      editor.onDidChangeCursorPosition((e) => {
        setCursorPosition({
          line: e.position.lineNumber,
          column: e.position.column,
        });
      });
    },
    [],
  );

  const handleEditorChange = (value: string | undefined) => {
    if (selectedPath && value) modifyFileContent(selectedPath, value);
  };

  React.useEffect(() => {
    const handleSave = async (event: KeyboardEvent) => {
      if (selectedPath && event.metaKey && event.key === "s") {
        const content = saveNewFileContent(selectedPath);

        if (content) {
          try {
            await OpenHands.saveFile(selectedPath, content);
          } catch (error) {
            toast.error("Failed to save file");
          }
        }
      }
    };

    document.addEventListener("keydown", handleSave);
    return () => {
      document.removeEventListener("keydown", handleSave);
    };
  }, [saveNewFileContent, selectedPath]);

  if (!selectedPath) {
    return (
      <div
        data-testid="code-editor-empty-message"
        className="flex flex-col h-full items-center justify-center text-neutral-400"
      >
        <VscCode size={100} />
        {t(I18nKey.CODE_EDITOR$EMPTY_MESSAGE)}
      </div>
    );
  }

  return (
    <div className="flex grow flex-col h-full w-full">
      {/* Ensure that the editor takes up the maximum amount of space in the parent container */}
      <div className="flex-grow min-h-0">
        <Editor
          data-testid="code-editor"
          height="100%"
          path={selectedPath ?? undefined}
          defaultValue=""
          value={
            selectedPath
              ? modifiedFiles[selectedPath] || files[selectedPath]
              : undefined
          }
          onMount={handleEditorDidMount}
          onChange={handleEditorChange}
          options={{ readOnly: isReadOnly }}
        />
      </div>
      {/* cursor position information */}
      <div className="p-2 text-neutral-500 flex-shrink-0">
        Row: {cursorPosition.line}, Column: {cursorPosition.column}
      </div>
    </div>
  );
}

export default React.memo(CodeEditorCompoonent);
