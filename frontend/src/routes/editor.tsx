import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { useConversation } from "#/context/conversation-context";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

function StatusMessage({ children }: React.PropsWithChildren) {
  return (
    <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
      {children}
    </div>
  );
}

function EditorScreen() {
  const { conversationId } = useConversation();
  const {
    data: gitChanges,
    isFetching,
    isSuccess,
    isError,
    error,
  } = useQuery({
    queryKey: ["file_changes", conversationId],
    queryFn: () => OpenHands.getGitChanges(conversationId),
    retry: false,
    meta: {
      disableToast: true,
    },
  });

  const isNotGitRepoError =
    isError && retrieveAxiosErrorMessage(error) === "Not a git repository";

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col">
      {isFetching && <div>Loading...</div>}
      {!isNotGitRepoError && isError && (
        <StatusMessage>{retrieveAxiosErrorMessage(error)}</StatusMessage>
      )}
      {isNotGitRepoError && (
        <StatusMessage>
          Your current workspace is not a git repository.
          <br />
          Ask OpenHands to initialize a git repo to activate this UI.
        </StatusMessage>
      )}

      {!isError && gitChanges?.length === 0 && (
        <StatusMessage>
          OpenHands hasn&apos;t made any changes yet...
        </StatusMessage>
      )}
      {isSuccess &&
        gitChanges.map((change) => (
          <FileDiffViewer
            key={change.path}
            path={change.path}
            type={change.status}
          />
        ))}
    </main>
  );
}

export default EditorScreen;
