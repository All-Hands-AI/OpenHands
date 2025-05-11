import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import React from "react";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { useGetGitChanges } from "#/hooks/query/use-get-git-changes";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { RandomTip } from "#/components/features/tips/random-tip";

// Error message patterns
const GIT_REPO_ERROR_PATTERN = /not a git repository/i;

function StatusMessage({ children }: React.PropsWithChildren) {
  return (
    <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
      {children}
    </div>
  );
}

function GitChanges() {
  const { t } = useTranslation();
  const { data: gitChanges, isSuccess, isError, error } = useGetGitChanges();

  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const runtimeIsActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const isNotGitRepoError =
    error && GIT_REPO_ERROR_PATTERN.test(retrieveAxiosErrorMessage(error));

  let statusMessage: React.ReactNode = null;
  if (!runtimeIsActive) {
    statusMessage = <span>{t(I18nKey.DIFF_VIEWER$WAITING_FOR_RUNTIME)}</span>;
  } else if (isNotGitRepoError) {
    if (error) {
      statusMessage = <span>{retrieveAxiosErrorMessage(error)}</span>;
    } else {
      statusMessage = (
        <span>
          {t(I18nKey.DIFF_VIEWER$NOT_A_GIT_REPO)}
          <br />
          {t(I18nKey.DIFF_VIEWER$ASK_OH)}
        </span>
      );
    }
  }

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col items-center">
      {!isSuccess || !gitChanges.length ? (
        <div className="relative flex h-full w-full items-center">
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2">
            {statusMessage && <StatusMessage>{statusMessage}</StatusMessage>}
          </div>

          <div className="absolute inset-x-0 bottom-0">
            {!isError && gitChanges?.length === 0 && (
              <div className="max-w-2xl mb-4 text-m bg-tertiary rounded-xl p-4 text-left mx-auto">
                <RandomTip />
              </div>
            )}
          </div>
        </div>
      ) : (
        gitChanges.map((change) => (
          <FileDiffViewer
            key={change.path}
            path={change.path}
            type={change.status}
          />
        ))
      )}
    </main>
  );
}

export default GitChanges;
