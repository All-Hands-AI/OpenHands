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
  onEdit: () => void;
  onDelete: () => void;
}

export function SecretListItem({
  title,
  onEdit,
  onDelete,
}: SecretListItemProps) {
  return (
    <div
      data-testid="secret-item"
      className="border-t border-[#717888] last-of-type:border-b max-w-[830px] pr-2.5 py-[13px] flex items-center justify-between"
    >
      <div className="flex items-center justify-between w-1/3">
        <span className="text-content-2 text-sm">{title}</span>
        <span className="text-content-2 text-sm italic opacity-80">
          {"<hidden>"}
        </span>
      </div>

      <div className="flex items-center gap-8">
        <button data-testid="edit-secret-button" type="button" onClick={onEdit}>
          <FaPencil width={18} height={18} />
        </button>
        <button
          data-testid="delete-secret-button"
          type="button"
          onClick={onDelete}
        >
          <FaTrash width={18} height={18} />
        </button>
      </div>
    </div>
  );
}
