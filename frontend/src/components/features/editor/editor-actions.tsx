import { EditorActionButton } from "#/components/shared/buttons/editor-action-button";

interface EditorActionsProps {
  onSave: () => void;
  onDiscard: () => void;
  isDisabled: boolean;
}

export function EditorActions({
  onSave,
  onDiscard,
  isDisabled,
}: EditorActionsProps) {
  return (
    <div className="flex gap-2">
      <EditorActionButton
        onClick={onSave}
        disabled={isDisabled}
        className="bg-neutral-800 disabled:hover:bg-neutral-800"
      >
        Save
      </EditorActionButton>

      <EditorActionButton
        onClick={onDiscard}
        disabled={isDisabled}
        className="border border-neutral-800 disabled:hover:bg-transparent"
      >
        Discard
      </EditorActionButton>
    </div>
  );
}
