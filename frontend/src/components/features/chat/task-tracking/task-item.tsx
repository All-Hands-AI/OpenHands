import { useTranslation } from "react-i18next";
import { Typography } from "#/ui/typography";
import { StatusIcon } from "./status-icon";
import { StatusBadge } from "./status-badge";

interface TaskItemProps {
  task: {
    id: string;
    title: string;
    status: "todo" | "in_progress" | "done";
    notes?: string;
  };
  index: number;
}

export function TaskItem({ task, index }: TaskItemProps) {
  const { t } = useTranslation();

  return (
    <div className="border-l-2 border-gray-600 pl-3">
      <div className="flex items-start gap-2">
        <StatusIcon status={task.status} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Typography.Text className="text-sm text-gray-400">
              {index + 1}.
            </Typography.Text>
            <StatusBadge status={task.status} />
          </div>
          <h4 className="font-medium text-white mb-1">{task.title}</h4>
          <Typography.Text className="text-xs text-gray-400 mb-1">
            {t("TASK_TRACKING_OBSERVATION$TASK_ID")}: {task.id}
          </Typography.Text>
          {task.notes && (
            <Typography.Text className="text-sm text-gray-300 italic">
              {t("TASK_TRACKING_OBSERVATION$TASK_NOTES")}: {task.notes}
            </Typography.Text>
          )}
        </div>
      </div>
    </div>
  );
}
