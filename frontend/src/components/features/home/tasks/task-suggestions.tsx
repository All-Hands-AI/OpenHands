import { useState } from "react";
import { useTranslation } from "react-i18next";
import { TaskGroup } from "./task-group";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import { GitRepository } from "#/types/git";
import { SuggestedTaskGroup } from "./task.types";

interface TaskSuggestionsProps {
  filterFor?: GitRepository | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);
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

  // Get the task groups to display based on expanded state
  let displayedTaskGroups: SuggestedTaskGroup[] = [];
  if (suggestedTasks && suggestedTasks.length > 0) {
    if (isExpanded) {
      displayedTaskGroups = suggestedTasks;
    } else {
      displayedTaskGroups = suggestedTasks.slice(0, 3);
    }
  }

  // Check if there are more task groups to show
  const hasMoreTaskGroups = suggestedTasks && suggestedTasks.length > 3;

  const handleToggle = () => {
    setIsExpanded((prev) => !prev);
  };

  return (
    <section data-testid="task-suggestions" className="flex flex-col w-full">
      <div
        className={cn(
          "flex items-center gap-2",
          !hasSuggestedTasks && "mb-[14px]",
        )}
      >
        <h3 className="text-xs leading-4 text-white font-bold py-[14px] pl-4">
          {t(I18nKey.TASKS$SUGGESTED_TASKS)}
        </h3>
      </div>

      <div className="flex flex-col">
        {isLoading && <TaskSuggestionsSkeleton />}
        {!hasSuggestedTasks && !isLoading && (
          <span className="text-xs leading-4 text-white font-medium pl-4">
            {t(I18nKey.TASKS$NO_TASKS_AVAILABLE)}
          </span>
        )}

        {!isLoading &&
          displayedTaskGroups &&
          displayedTaskGroups.length > 0 && (
            <div className="flex flex-col">
              <div className="transition-all duration-300 ease-in-out max-h-[420px] overflow-y-auto custom-scrollbar">
                <div className="flex flex-col">
                  {displayedTaskGroups.map((taskGroup, index) => (
                    <TaskGroup
                      key={index}
                      title={decodeURIComponent(taskGroup.title)}
                      tasks={taskGroup.tasks}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
      </div>

      {!isLoading && hasMoreTaskGroups && (
        <div className="flex justify-start mt-6 mb-8 ml-4">
          <button
            type="button"
            onClick={handleToggle}
            className="text-xs leading-4 text-[#FAFAFA] font-normal cursor-pointer hover:underline"
          >
            {isExpanded
              ? t(I18nKey.COMMON$VIEW_LESS)
              : t(I18nKey.COMMON$VIEW_MORE)}
          </button>
        </div>
      )}
    </section>
  );
}
