import { TaskGroup } from "./task-group";
import { NoSuggestedTasksMessage } from "./no-suggested-tasks-message";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";

interface TaskSuggestionsProps {
  filterFor?: string | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { data: tasks, isLoading } = useSuggestedTasks();
  const suggestedTasks = filterFor
    ? tasks?.filter((task) => task.title === filterFor)
    : tasks;

  return (
    <section data-testid="task-suggestions" className="flex flex-col w-full">
      <h2 className="heading">Suggested Tasks</h2>

      <div className="flex flex-col gap-6 overflow-y-auto">
        {isLoading && <TaskSuggestionsSkeleton />}
        {suggestedTasks?.length === 0 && <NoSuggestedTasksMessage />}
        {suggestedTasks?.map((taskGroup, index) => (
          <TaskGroup
            key={index}
            title={taskGroup.title}
            tasks={taskGroup.tasks}
          />
        ))}
      </div>
    </section>
  );
}
