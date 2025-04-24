interface SecretListItemProps {
  title: string;
  onEdit: () => void;
  onDelete: () => void;
}

export function SecretListItem({
  title,
  onEdit,
  onDelete,
}: SecretListItemProps) {
  return (
    <div data-testid="secret-item">
      {title}

      <button data-testid="edit-secret-button" type="button" onClick={onEdit}>
        Edit Secret
      </button>

      <button
        data-testid="delete-secret-button"
        type="button"
        onClick={onDelete}
      >
        Delete Secret
      </button>
    </div>
  );
}
