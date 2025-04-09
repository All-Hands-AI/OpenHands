import { useQuery } from "@tanstack/react-query";
import { TaskGroup } from "./task-group";
import { SuggestionsService } from "#/api/suggestions-service/suggestions-service.api";
import { NoSuggestedTasksMessage } from "./no-suggested-tasks-message";

export function TaskSuggestions() {
  const { data: suggestedTasks } = useQuery({
    queryKey: ["tasks"],
    queryFn: SuggestionsService.getSuggestedTasks,
  });

  return (
    <section className="flex flex-col w-full">
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
