import { useQuery } from "@tanstack/react-query";
import { TaskGroup } from "./task-group";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { NoSuggestedTasksMessage } from "./no-suggested-tasks-message";
import { groupSuggestedTasks } from "#/utils/group-suggested-tasks";

interface TaskSuggestionsProps {
  filterFor?: string | null;
}

export function TaskSuggestions({ filterFor }: TaskSuggestionsProps) {
  const { data: tasks } = useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
    select: groupSuggestedTasks,
  });

  const suggestedTasks = filterFor
    ? tasks?.filter((task) => task.title === filterFor)
    : tasks;

  return (
    <section data-testid="task-suggestions" className="flex flex-col w-full">
      <h2 className="heading">Suggested Tasks</h2>

      <div className="flex flex-col gap-6 overflow-y-auto">
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
