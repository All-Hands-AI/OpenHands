import React, { createContext, useContext, ReactNode } from "react";
import { useFileState, FileState } from "#/hooks/state/use-file-state";

export interface FileStateContextType {
  fileStates: FileState[];
  addOrUpdateFileState: (fileState: Omit<FileState, "changed">) => void;
  removeFileState: (path: string) => void;
  isFileChanged: (path: string) => boolean;
  getFileState: (path: string) => FileState | undefined;
  resetFileStates: () => void;
  // Added for compatibility with old Redux state
  selectedRepository: string | null;
  files: string[];
}

const FileStateContext = createContext<FileStateContextType | undefined>(
  undefined,
);

/**
 * Provider component for file state
 */
export function FileStateProvider({ children }: { children: ReactNode }) {
  const fileState = useFileState();

  return (
    <FileStateContext.Provider value={fileState}>
      {children}
    </FileStateContext.Provider>
  );
}

/**
 * Hook to use the file state context
 */
export function useFileStateContext() {
  const context = useContext(FileStateContext);

  if (context === undefined) {
    throw new Error(
      "useFileStateContext must be used within a FileStateProvider",
    );
  }

  return context;
}
