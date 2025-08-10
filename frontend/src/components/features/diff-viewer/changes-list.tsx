/* eslint-disable i18next/no-literal-string */
import React from "react";
import { useGetGitChanges } from "#/hooks/query/use-get-git-changes";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { BrandButton } from "#/components/features/settings/brand-button";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";

export function ChangesList() {
  const { data: changes, isSuccess } = useGetGitChanges();
  const [selected, setSelected] = React.useState<Record<string, boolean>>({});
  const [message, setMessage] = React.useState("");
  const { conversationId } = useConversationId();

  const toggle = (path: string) =>
    setSelected((prev) => ({ ...prev, [path]: !prev[path] }));

  const commitSelected = async () => {
    const files = Object.keys(selected).filter((k) => selected[k]);
    if (!files.length || !message.trim()) return;
    await OpenHands.commitChanges(conversationId, message, files);
    setMessage("");
    setSelected({});
  };

  if (!isSuccess || !changes?.length) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <input
          className="bg-tertiary border border-tertiary-alt rounded px-2 py-1 w-96"
          placeholder="Commit message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <BrandButton variant="primary" type="button" onClick={commitSelected}>
          Commit Selected
        </BrandButton>
      </div>
      {changes.map((change) => (
        <div key={change.path} className="border border-tertiary rounded">
          <label className="flex items-center gap-2 p-2">
            <input
              type="checkbox"
              checked={!!selected[change.path]}
              onChange={() => toggle(change.path)}
            />
            <span className="text-sm">{change.path}</span>
          </label>
          <FileDiffViewer path={change.path} type={change.status} />
        </div>
      ))}
    </div>
  );
}
