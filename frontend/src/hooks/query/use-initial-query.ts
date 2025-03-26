import { useQuery, useQueryClient } from "@tanstack/react-query";

interface InitialQueryState {
  files: string[];
  initialPrompt: string | null;
  selectedRepository: string | null;
  replayJson: string | null;
}

const initialState: InitialQueryState = {
  files: [],
  initialPrompt: null,
  selectedRepository: null,
  replayJson: null,
};

export const INITIAL_QUERY_KEY = ["initialQuery"];

export function updateInitialQueryState(
  queryClient: ReturnType<typeof useQueryClient>,
  updater: (state: InitialQueryState) => InitialQueryState,
) {
  const currentState =
    queryClient.getQueryData<InitialQueryState>(INITIAL_QUERY_KEY) ||
    initialState;
  const newState = updater(currentState);
  queryClient.setQueryData(INITIAL_QUERY_KEY, newState);
}

export function useInitialQuery() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: INITIAL_QUERY_KEY,
    queryFn: () => {
      const existingData =
        queryClient.getQueryData<InitialQueryState>(INITIAL_QUERY_KEY);
      if (existingData) return existingData;
      return initialState;
    },
    initialData: initialState,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const addFile = (file: string) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      files: [...state.files, file],
    }));
  };

  const removeFile = (index: number) => {
    updateInitialQueryState(queryClient, (state) => {
      const newFiles = [...state.files];
      newFiles.splice(index, 1);
      return {
        ...state,
        files: newFiles,
      };
    });
  };

  const clearFiles = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      files: [],
    }));
  };

  const setInitialPrompt = (prompt: string) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      initialPrompt: prompt,
    }));
  };

  const clearInitialPrompt = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      initialPrompt: null,
    }));
  };

  const setSelectedRepository = (repository: string | null) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      selectedRepository: repository,
    }));
  };

  const clearSelectedRepository = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      selectedRepository: null,
    }));
  };

  const setReplayJson = (replayJson: string | null) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      replayJson,
    }));
  };

  return {
    files: query.data?.files || initialState.files,
    initialPrompt: query.data?.initialPrompt || initialState.initialPrompt,
    selectedRepository:
      query.data?.selectedRepository || initialState.selectedRepository,
    isLoading: query.isLoading,
    replayJson: query.data?.replayJson || initialState.replayJson,

    addFile,
    removeFile,
    clearFiles,
    setInitialPrompt,
    clearInitialPrompt,
    setSelectedRepository,
    clearSelectedRepository,
    setReplayJson,
  };
}
