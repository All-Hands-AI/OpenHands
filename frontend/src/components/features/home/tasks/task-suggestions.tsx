import { TaskGroup } from "./task-group";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";
import { cn } from "#/utils/utils";

interface TaskSuggestionsProps {
  filterFor?: string | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { data: tasks, isLoading } = useSuggestedTasks();
  const suggestedTasks = filterFor
    ? tasks?.filter((task) => task.title === filterFor)
    : tasks;

  const hasSuggestedTasks = suggestedTasks && suggestedTasks.length > 0;

  return (
    <section
      data-testid="task-suggestions"
      className={cn("flex flex-col w-full", !hasSuggestedTasks && "gap-6")}
    >
      <h2 className="heading">Suggested Tasks</h2>

      <div className="flex flex-col gap-6">
        {isLoading && <TaskSuggestionsSkeleton />}
        {!hasSuggestedTasks && !isLoading && <p>No tasks available</p>}
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
