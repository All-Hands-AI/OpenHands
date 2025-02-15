import React from "react";

interface FilesContextType {
  /**
   * List of file paths in the workspace
   */
  paths: string[];
  /**
   * Set the list of file paths in the workspace
   * @param paths The list of file paths in the workspace
   * @returns void
   */
  setPaths: (paths: string[]) => void;
  /**
   * A map of file paths to their contents
   */
  files: Record<string, string>;
  /**
   * Set the content of a file
   * @param path The path of the file
   * @param content The content of the file
   * @returns void
   */
  setFileContent: (path: string, content: string) => void;
  selectedPath: string | null;
  setSelectedPath: (path: string | null) => void;
}

const FilesContext = React.createContext<FilesContextType | undefined>(
  undefined,
);

interface FilesProviderProps {
  children: React.ReactNode;
}

function FilesProvider({ children }: FilesProviderProps) {
  const [paths, setPaths] = React.useState<string[]>([]);
  const [files, setFiles] = React.useState<Record<string, string>>({});
  const [selectedPath, setSelectedPath] = React.useState<string | null>(null);

  const setFileContent = React.useCallback((path: string, content: string) => {
    setFiles((prev) => ({ ...prev, [path]: content }));
  }, []);

  const value = React.useMemo(
    () => ({
      paths,
      setPaths,
      files,
      setFileContent,
      selectedPath,
      setSelectedPath,
    }),
    [paths, setPaths, files, setFileContent, selectedPath, setSelectedPath],
  );

  return <FilesContext value={value}>{children}</FilesContext>;
}

function useFiles() {
  const context = React.useContext(FilesContext);
  if (context === undefined) {
    throw new Error("useFiles must be used within a FilesProvider");
  }
  return context;
}

export { FilesProvider, useFiles };
