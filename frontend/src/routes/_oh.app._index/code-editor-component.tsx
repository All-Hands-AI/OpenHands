import { Editor, EditorProps } from "@monaco-editor/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { VscCode } from "react-icons/vsc";
import { I18nKey } from "#/i18n/declaration";
import { useFiles } from "#/context/files";
import { useSaveFile } from "#/hooks/mutation/use-save-file";

interface CodeEditorComponentProps {
  onMount: EditorProps["onMount"];
  isReadOnly: boolean;
}

function CodeEditorComponent({
  onMount,
  isReadOnly,
}: CodeEditorComponentProps) {
  const { t } = useTranslation();
  const {
    files,
    selectedPath,
    modifiedFiles,
    modifyFileContent,
    saveFileContent: saveNewFileContent,
  } = useFiles();

  const { mutate: saveFile } = useSaveFile();

  const handleEditorChange = (value: string | undefined) => {
    if (selectedPath && value) modifyFileContent(selectedPath, value);
  };

  const isBase64Image = (content: string) => content.startsWith("data:image/");
  const isPDF = (content: string) => content.startsWith("data:application/pdf");
  const isVideo = (content: string) => content.startsWith("data:video/");

  React.useEffect(() => {
    const handleSave = async (event: KeyboardEvent) => {
      if (selectedPath && event.metaKey && event.key === "s") {
        const content = saveNewFileContent(selectedPath);

        if (content) {
          saveFile({ path: selectedPath, content });
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

  const fileContent: string | undefined =
    modifiedFiles[selectedPath] || files[selectedPath];

  if (fileContent) {
    if (isBase64Image(fileContent)) {
      return (
        <section className="flex flex-col relative items-center overflow-auto h-[90%]">
          <img
            src={fileContent}
            alt={selectedPath}
            className="object-contain"
          />
        </section>
      );
    }

    if (isPDF(fileContent)) {
      return (
        <iframe
          src={fileContent}
          title={selectedPath}
          width="100%"
          height="100%"
        />
      );
    }

    if (isVideo(fileContent)) {
      return (
        <video controls src={fileContent} width="100%" height="100%">
          <track kind="captions" label="English captions" />
        </video>
      );
    }
  }

  return (
    <Editor
      data-testid="code-editor"
      path={selectedPath ?? undefined}
      defaultValue=""
      value={selectedPath ? fileContent : undefined}
      onMount={onMount}
      onChange={handleEditorChange}
      options={{ readOnly: isReadOnly }}
    />
  );
}

export default React.memo(CodeEditorComponent);
