import { Editor, EditorProps } from "@monaco-editor/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
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
  }, [saveNewFileContent]);

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
    <Editor
      data-testid="code-editor"
      path={selectedPath ?? undefined}
      defaultValue=""
      value={
        selectedPath
          ? modifiedFiles[selectedPath] || files[selectedPath]
          : undefined
      }
      onMount={onMount}
      onChange={handleEditorChange}
      options={{ readOnly: isReadOnly }}
    />
  );
}

export default React.memo(CodeEditorCompoonent);
