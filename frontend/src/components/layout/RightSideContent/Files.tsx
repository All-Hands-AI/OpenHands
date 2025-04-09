import { FilesProvider } from "#/context/files";
import { useListFiles } from "#/hooks/query/use-list-files";
import TestFileViewer from "./TestFileViewer";

const Files = () => {
  const { data: paths, refetch, error } = useListFiles();

  return (
    <FilesProvider>
      {paths &&
        Array.isArray(paths) &&
        paths.map((path: string) => <TestFileViewer currentPath={path} />)}
    </FilesProvider>
  );
};

export default Files;
