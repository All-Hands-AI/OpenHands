export type ConversationCardTitleMode = "view" | "edit";

export type ConversationCardTitleProps = {
  titleMode: ConversationCardTitleMode;
  title: string;
  onSave: (title: string) => void;
};

export function ConversationCardTitle({
  titleMode,
  title,
  onSave,
}: ConversationCardTitleProps) {
  if (titleMode === "edit") {
    return (
      <input
        /* eslint-disable jsx-a11y/no-autofocus */
        autoFocus
        data-testid="conversation-card-title"
        onClick={(event: React.MouseEvent<HTMLInputElement>) => {
          event.preventDefault();
          event.stopPropagation();
        }}
        onBlur={(e) => {
          const trimmed = e.currentTarget?.value?.trim?.() ?? "";
          onSave(trimmed);
        }}
        onKeyUp={(event: React.KeyboardEvent<HTMLInputElement>) => {
          if (event.key === "Enter") {
            event.currentTarget.blur();
          }
        }}
        type="text"
        defaultValue={title}
        className="text-sm leading-6 font-semibold bg-transparent w-full"
      />
    );
  }

  return (
    <p
      data-testid="conversation-card-title"
      className="text-xs leading-6 font-semibold bg-transparent truncate overflow-hidden"
      title={title}
    >
      {title}
    </p>
  );
}
