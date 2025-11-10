import { useTranslation } from "react-i18next";
import { TaskItem } from "./task-item";
import { Typography } from "#/ui/typography";

interface TaskListSectionProps {
  taskList: Array<{
    id: string;
    title: string;
    status: "todo" | "in_progress" | "done";
    notes?: string;
  }>;
}

export function TaskListSection({ taskList }: TaskListSectionProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <Typography.H3>
          {t("TASK_TRACKING_OBSERVATION$TASK_LIST")} ({taskList.length}{" "}
          {taskList.length === 1 ? "item" : "items"})
        </Typography.H3>
      </div>
      <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 max-h-[400px] shadow-inner">
        <div className="space-y-3">
          {taskList.map((task, index) => (
            <TaskItem key={task.id} task={task} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
}
