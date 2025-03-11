import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { useConversation } from "#/context/conversation-context";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

interface StatusMessageProps {
  message: string;
}

function StatusMessage({ message }: StatusMessageProps) {
  return (
    <div className="w-full h-full flex items-center justify-center text-2xl text-tertiary-light">
      {message}
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

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col">
      {isFetching && <div>Loading...</div>}
      {isError && <StatusMessage message={retrieveAxiosErrorMessage(error)} />}

      {!isError && gitChanges?.length === 0 && (
        <StatusMessage message="Clean working tree" />
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
