import { TaskTrackingObservation } from "#/types/core/observations";
import { TaskListSection } from "./task-tracking/task-list-section";
import { ResultSection } from "./task-tracking/result-section";

interface TaskTrackingObservationContentProps {
  event: TaskTrackingObservation;
}

export function TaskTrackingObservationContent({
  event,
}: TaskTrackingObservationContentProps) {
  const { command, task_list: taskList } = event.extras;
  const shouldShowTaskList = command === "plan" && taskList.length > 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Task List section - only show for 'plan' command */}
      {shouldShowTaskList && <TaskListSection taskList={taskList} />}

      {/* Result message - only show if there's meaningful content */}
      {event.content && event.content.trim() && (
        <ResultSection content={event.content} />
      )}
    </div>
  );
}
