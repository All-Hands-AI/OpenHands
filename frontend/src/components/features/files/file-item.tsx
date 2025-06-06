import { RemoveButton } from "#/components/shared/buttons/remove-button";

interface FileItemProps {
  filename: string;
  onRemove?: () => void;
}

export function FileItem({ filename, onRemove }: FileItemProps) {
  return (
    <div
      data-testid="file-item"
      className="flex flex-row items-center justify-start"
    >
      <span className="text-sm flex-1 text-white">{filename}</span>
      {onRemove && <RemoveButton onClick={onRemove} />}
    </div>
  );
}
