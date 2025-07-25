import { Typography } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import { TaskGroup } from "./task-group";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
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
      className={cn(
        "flex flex-col w-full pr-[16px] py-[10.5px]",
        !hasSuggestedTasks && "gap-6",
      )}
    >
      <div className="flex items-center gap-2">
        <Typography.H2 className="text-sm leading-[16px] text-white font-medium">
          {t(I18nKey.TASKS$SUGGESTED_TASKS)}
        </Typography.H2>
      </div>

      <div className="flex flex-col">
        {isLoading && <TaskSuggestionsSkeleton />}
        {!hasSuggestedTasks && !isLoading && (
          <Typography.Text className="text-sm leading-[16px] text-white font-medium">
            {t(I18nKey.TASKS$NO_TASKS_AVAILABLE)}
          </Typography.Text>
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
