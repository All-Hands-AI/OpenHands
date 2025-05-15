import { FaPencil, FaTrash } from "react-icons/fa6";

export function SecretListItemSkeleton() {
  return (
    <div className="border-t border-[#717888] last-of-type:border-b max-w-[830px] pr-2.5 py-[13px] flex items-center justify-between">
      <div className="flex items-center justify-between w-1/3">
        <span className="skeleton h-4 w-1/2" />
        <span className="skeleton h-4 w-1/4" />
      </div>

      <div className="flex items-center gap-8">
        <span className="skeleton h-4 w-4" />
        <span className="skeleton h-4 w-4" />
      </div>
    </div>
  );
}

interface SecretListItemProps {
  title: string;
  description?: string;
  onEdit: () => void;
  onDelete: () => void;
}

export function SecretListItem({
  title,
  description,
  onEdit,
  onDelete,
}: SecretListItemProps) {
  return (
    <tr
      data-testid="secret-item"
      className="border-t border-[#717888] last-of-type:border-b max-w-[830px] py-[13px] flex w-full items-center"
    >
      <td className="w-1/4 text-sm text-content-2">{title}</td>

      <td className="w-1/2 truncate overflow-hidden whitespace-nowrap text-sm text-content-2 opacity-80 italic">
        {description || "-"}
      </td>

      <td className="w-1/4 flex items-center justify-end gap-4">
        <button
          data-testid="edit-secret-button"
          type="button"
          onClick={onEdit}
          aria-label={`Edit ${title}`}
        >
          <FaPencil size={16} />
        </button>
        <button
          data-testid="delete-secret-button"
          type="button"
          onClick={onDelete}
          aria-label={`Delete ${title}`}
        >
          <FaTrash size={16} />
        </button>
      </td>
    </tr>
  );
}
