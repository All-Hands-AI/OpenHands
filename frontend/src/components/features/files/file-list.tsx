import React from "react";
import { cn } from "#/utils/utils";
import { FileItem } from "./file-item";

type FileItemType = {
  filename: string;
  id?: string;
};

interface FileListProps {
  files: FileItemType[];
  onRemove?: (id: string) => void;
}

export function FileList({ files, onRemove }: FileListProps) {
  return (
    <div
      data-testid="file-list"
      className={cn("flex flex-col gap-y-1.5 justify-start")}
    >
      {files.map((f, index) => (
        <FileItem
          key={index}
          filename={f.filename}
          onRemove={onRemove ? () => onRemove(f.id!) : undefined}
        />
      ))}
    </div>
  );
}
