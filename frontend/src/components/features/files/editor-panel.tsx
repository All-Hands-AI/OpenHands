/* eslint-disable i18next/no-literal-string */
import React from "react";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "#/components/features/settings/brand-button";

interface EditorPanelProps {
  conversationId: string;
  path: string | null;
}

export function EditorPanel({ conversationId, path }: EditorPanelProps) {
  const [content, setContent] = React.useState("");
  const [isDirty, setIsDirty] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  React.useEffect(() => {
    const load = async () => {
      if (!path) return;
      setIsLoading(true);
      try {
        const data = await OpenHands.readRepoFile(conversationId, path);
        setContent(data.content);
        setIsDirty(false);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [conversationId, path]);

  const onSave = async () => {
    if (!path) return;
    await OpenHands.writeRepoFile(conversationId, path, content);
    setIsDirty(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-tertiary px-3 py-2">
        <div className="text-sm opacity-80">{path || "No file selected"}</div>
        <div className="flex gap-2">
          <BrandButton
            variant="primary"
            type="button"
            isDisabled={!isDirty || !path || isLoading}
            onClick={onSave}
          >
            Save
          </BrandButton>
        </div>
      </div>
      <textarea
        className="flex-1 w-full p-3 font-mono text-sm bg-tertiary outline-none"
        value={content}
        spellCheck={false}
        onChange={(e) => {
          setContent(e.target.value);
          setIsDirty(true);
        }}
      />
    </div>
  );
}
