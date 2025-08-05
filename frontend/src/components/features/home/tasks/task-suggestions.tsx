import { useTranslation } from "react-i18next";
import { FaInfoCircle } from "react-icons/fa";
import { TaskGroup } from "./task-group";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { GitRepository } from "#/types/git";

interface TaskSuggestionsProps {
  filterFor?: GitRepository | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { t } = useTranslation();
  const { data: tasks, isLoading } = useSuggestedTasks();

  const suggestedTasks = filterFor
    ? tasks?.filter(
        (element) =>
          element.title === filterFor.full_name &&
          !!element.tasks.find(
            (task) => task.git_provider === filterFor.git_provider,
          ),
      )
    : tasks;

  const hasSuggestedTasks = suggestedTasks && suggestedTasks.length > 0;

  return (
    <section
      data-testid="task-suggestions"
      className={cn("flex flex-col w-full", !hasSuggestedTasks && "gap-6")}
    >
      <div className="flex items-center gap-2">
        <h2 className="heading">{t(I18nKey.TASKS$SUGGESTED_TASKS)}</h2>
        <TooltipButton
          testId="task-suggestions-info"
          tooltip={t(I18nKey.TASKS$TASK_SUGGESTIONS_TOOLTIP)}
          ariaLabel={t(I18nKey.TASKS$TASK_SUGGESTIONS_INFO)}
          className="text-[#9099AC] hover:text-white"
          placement="bottom"
          tooltipClassName="max-w-[348px]"
        >
          <FaInfoCircle size={16} />
        </TooltipButton>
      </div>

      <div className="flex flex-col gap-6">
        {isLoading && <TaskSuggestionsSkeleton />}
        {!hasSuggestedTasks && !isLoading && (
          <p>{t(I18nKey.TASKS$NO_TASKS_AVAILABLE)}</p>
        )}
        {suggestedTasks?.map((taskGroup, index) => (
          <TaskGroup
            key={index}
            title={decodeURIComponent(taskGroup.title)}
            tasks={taskGroup.tasks}
          />
        ))}
      </div>
    </section>
  );
}
