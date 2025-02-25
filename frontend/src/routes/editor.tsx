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

  const paths = Object.keys(diffs);

  return (
    <main className="h-full overflow-y-auto px-4">
      {paths.map((path) => (
        <FileDiffViewer
          key={path}
          label={path}
          modified={diffs[path].full_content}
          original={diffs[path].last_commit_content}
        />
      ))}
    </main>
  );
}

export default EditorScreen;
