import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { TaskListSection } from "#/components/features/chat/task-tracking/task-list-section";
import { useGetTasks } from "#/hooks/query/use-get-tasks";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { RandomTip } from "#/components/features/tips/random-tip";

function StatusMessage({ children }: React.PropsWithChildren) {
  return (
    <div className="w-full h-full flex flex-col items-center text-center justify-center text-2xl text-tertiary-light">
      {children}
    </div>
  );
}

function TasksTab() {
  const { t } = useTranslation();
  const {
    data: tasks,
    isSuccess,
    isError,
    error,
    isLoading: loadingTasks,
  } = useGetTasks();

  const [statusMessage, setStatusMessage] = React.useState<string[] | null>(
    null,
  );

  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const runtimeIsActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  React.useEffect(() => {
    if (!runtimeIsActive) {
      setStatusMessage([I18nKey.DIFF_VIEWER$WAITING_FOR_RUNTIME]);
    } else if (error) {
      setStatusMessage([I18nKey.COMMON$ERROR_LOADING_TASKS]);
    } else if (loadingTasks) {
      setStatusMessage([I18nKey.HOME$LOADING]);
    } else {
      setStatusMessage(null);
    }
  }, [runtimeIsActive, loadingTasks, error, setStatusMessage]);

  return (
    <main className="h-full overflow-y-scroll p-4 md:pr-1.5 gap-3 flex flex-col items-center custom-scrollbar-always">
      {!isSuccess || !tasks || tasks.length === 0 ? (
        <div className="relative flex h-full w-full items-center">
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2">
            {statusMessage && (
              <StatusMessage>
                {statusMessage.map((msg) => (
                  <span key={msg}>{t(msg)}</span>
                ))}
              </StatusMessage>
            )}
            {!statusMessage && isSuccess && tasks && tasks.length === 0 && (
              <StatusMessage>
                <span>{t(I18nKey.COMMON$NO_TASKS_AVAILABLE)}</span>
              </StatusMessage>
            )}
          </div>

          <div className="absolute inset-x-0 bottom-0">
            {!isError && tasks?.length === 0 && (
              <div className="max-w-2xl mb-4 text-m bg-tertiary rounded-xl p-4 text-left mx-auto">
                <RandomTip />
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="w-full max-w-4xl">
          <TaskListSection taskList={tasks} />
        </div>
      )}
    </main>
  );
}

export default TasksTab;
