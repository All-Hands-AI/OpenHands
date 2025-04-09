import { FilesProvider } from "#/context/files";
import { useListFiles } from "#/hooks/query/use-list-files";
import TestFileViewer from "./TestFileViewer";

const Files = () => {
  const { data: paths, refetch, error } = useListFiles();

  return (
    <FilesProvider>
      {paths &&
        Array.isArray(paths) && <TestFileViewer currentPath={paths?.[paths?.length -1]} />
      }
        {/* // paths.map((path: string) => <TestFileViewer currentPath={path} />)} */}
    </FilesProvider>
  );
};

export default Files;
