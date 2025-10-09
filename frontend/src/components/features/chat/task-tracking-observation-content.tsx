import { TaskListSection } from "./task-tracking/task-list-section";
import { ResultSection } from "./task-tracking/result-section";
import { TaskTrackerObservation } from "#/types/v1/core";

interface TaskTrackingObservationContentProps {
  event: {
    command: string;
    taskList: TaskTrackerObservation["task_list"];
    content: string;
  };
}

export function TaskTrackingObservationContent({
  event,
}: TaskTrackingObservationContentProps) {
  const { command, taskList } = event;
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
