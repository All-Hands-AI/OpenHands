import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { useConversation } from "#/context/conversation-context";

function EditorScreen() {
  const { conversationId } = useConversation();
  const {
    data: gitChanges,
    isLoading,
    isSuccess,
  } = useQuery({
    queryKey: ["file_changes", conversationId],
    queryFn: () => OpenHands.getGitChanges(conversationId),
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isSuccess || !gitChanges) {
    return <div>Failed to load diffs</div>;
  }

  return (
    <main className="h-full overflow-y-auto px-4">
      {gitChanges.map((change) => (
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
