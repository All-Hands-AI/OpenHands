import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { useGetGitChanges } from "#/hooks/query/use-get-git-changes";

function StatusMessage({ children }: React.PropsWithChildren) {
  return (
    <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
      {children}
    </div>
  );
}

function EditorScreen() {
  const { data: gitChanges, isSuccess, isError, error } = useGetGitChanges();

  const isNotGitRepoError =
    isError && retrieveAxiosErrorMessage(error) === "Not a git repository";

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col">
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
