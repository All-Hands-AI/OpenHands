import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { useConversation } from "#/context/conversation-context";

function EditorScreen() {
  const { conversationId } = useConversation();
  const {
    data: diffs,
    isLoading,
    isSuccess,
  } = useQuery({
    queryKey: ["diffs", conversationId],
    queryFn: () => OpenHands.getDiffs(conversationId),
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isSuccess || !diffs) {
    return <div>Failed to load diffs</div>;
  }

  return (
    <main className="h-full overflow-y-auto px-4">
      {diffs.map((diff) => (
        <FileDiffViewer
          key={diff.path}
          label={diff.path}
          modified={diff.modified}
          original={diff.original}
        />
      ))}
    </main>
  );
}

export default EditorScreen;
