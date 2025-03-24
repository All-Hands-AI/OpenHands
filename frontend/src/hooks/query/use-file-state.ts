import { useQuery, useQueryClient } from "@tanstack/react-query";

interface FileStateState {
  changed: Record<string, boolean>;
}

const initialFileState: FileStateState = {
  changed: {},
};

export function useFileState() {
  const queryClient = useQueryClient();

  const getInitialFileStateState = (): FileStateState => {
    const existingData = queryClient.getQueryData<FileStateState>(["file"]);
    if (existingData) return existingData;
    return initialFileState;
  };

  const query = useQuery({
    queryKey: ["fileState"],
    queryFn: () => {
      const existingData = queryClient.getQueryData<FileStateState>([
        "fileState",
      ]);
      if (existingData) return existingData;
      return getInitialFileStateState();
    },
    initialData: initialFileState,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const setChanged = (path: string, changed: boolean) => {
    const previousState =
      queryClient.getQueryData<FileStateState>(["fileState"]) ||
      initialFileState;

    const newState = {
      ...previousState,
      changed: {
        ...previousState.changed,
        [path]: changed,
      },
    };

    queryClient.setQueryData<FileStateState>(["fileState"], newState);
  };

  return {
    changed: query.data?.changed || initialFileState.changed,
    isLoading: query.isLoading,
    setChanged,
  };
}
