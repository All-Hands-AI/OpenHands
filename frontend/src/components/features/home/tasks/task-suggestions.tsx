import { TaskGroup } from "./task-group";
import { NoSuggestedTasksMessage } from "./no-suggested-tasks-message";
import { useSuggestedTasks } from "#/hooks/query/use-suggested-tasks";
import { TaskSuggestionsSkeleton } from "./task-suggestions-skeleton";
import { useAuth } from "#/context/auth-context";
import { cn } from "#/utils/utils";
import { ConnectToProviderMessage } from "../connect-to-provider-message";

interface TaskSuggestionsProps {
  filterFor?: string | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { providersAreSet } = useAuth();

  const { data: tasks, isLoading } = useSuggestedTasks();
  const suggestedTasks = filterFor
    ? tasks?.filter((task) => task.title === filterFor)
    : tasks;

  return (
    <section
      data-testid="task-suggestions"
      className={cn("flex flex-col w-full", !suggestedTasks && "gap-4")}
    >
      <h2 className="heading">Suggested Tasks</h2>

      <div className="flex flex-col gap-6 overflow-y-auto">
        {!providersAreSet && <ConnectToProviderMessage />}
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
