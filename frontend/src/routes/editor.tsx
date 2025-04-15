import { useTranslation } from "react-i18next";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { useGetGitChanges } from "#/hooks/query/use-get-git-changes";
import { I18nKey } from "#/i18n/declaration";

function StatusMessage({ children }: React.PropsWithChildren) {
  return (
    <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
      {children}
    </div>
  );
}

function EditorScreen() {
  const { t } = useTranslation();
  const { data: gitChanges, isSuccess, isError, error } = useGetGitChanges();

  const isNotGitRepoError =
    error && retrieveAxiosErrorMessage(error) === "Not a git repository";

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col">
      {!isNotGitRepoError && error && (
        <StatusMessage>{retrieveAxiosErrorMessage(error)}</StatusMessage>
      )}
      {isNotGitRepoError && (
        <StatusMessage>
          {t(I18nKey.DIFF_VIEWER$NOT_A_GIT_REPO)}
          <br />
          {t(I18nKey.DIFF_VIEWER$ASK_OH)}
        </StatusMessage>
      )}

      {!isError && gitChanges?.length === 0 && (
        <StatusMessage>{t(I18nKey.DIFF_VIEWER$NO_CHANGES)}</StatusMessage>
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
