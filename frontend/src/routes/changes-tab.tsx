import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import React from "react";
import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { useGetGitChanges } from "#/hooks/query/use-get-git-changes";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { getRandomTip } from "#/utils/tips";

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
  const [randomTip, setRandomTip] = React.useState(getRandomTip());

  // Update the random tip when the component mounts
  React.useEffect(() => {
    setRandomTip(getRandomTip());
  }, []);
  console.log("random tip", randomTip);

  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const runtimeIsActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const isNotGitRepoError =
    error && GIT_REPO_ERROR_PATTERN.test(retrieveAxiosErrorMessage(error));

  return (
    <main className="h-full overflow-y-scroll px-4 py-3 gap-3 flex flex-col items-center">
      {!runtimeIsActive && (
        <StatusMessage>
          {t(I18nKey.DIFF_VIEWER$WAITING_FOR_RUNTIME)}
        </StatusMessage>
      )}
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
        <div className="max-w-2xl flex">
          <div className="mb-4 text-m bg-tertiary rounded p-4 text-left">
            <p>
              <h4 className="font-bold">Protip:</h4>
              {t(randomTip.key)}
            </p>
          </div>
        </div>
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

export default GitChanges;
