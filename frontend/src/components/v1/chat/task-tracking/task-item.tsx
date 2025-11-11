import { useMemo } from "react";
import { TaskItem as TaskItemType } from "#/types/v1/core/base/common";
import CircleIcon from "#/icons/u-circle.svg?react";
import CheckCircleIcon from "#/icons/u-check-circle.svg?react";
import LoadingIcon from "#/icons/loading.svg?react";
import { cn } from "#/utils/utils";

interface TaskItemProps {
  task: TaskItemType;
}

export function TaskItem({ task }: TaskItemProps) {
  const icon = useMemo(() => {
    switch (task.status) {
      case "todo":
        return <CircleIcon className="w-4 h-4 text-[#ffffff]" />;
      case "in_progress":
        return <LoadingIcon className="w-4 h-4 text-[#ffffff]" />;
      case "done":
        return <CheckCircleIcon className="w-4 h-4 text-[#A3A3A3]" />;
      default:
        return <CircleIcon className="w-4 h-4 text-[#ffffff]" />;
    }
  }, [task.status]);

  const isDoneStatus = task.status === "done";

  return (
    <div className="flex items-center px-4 py-2 w-full" data-name="item">
      <div className="flex gap-[14px] items-center">
        <div className="shrink-0 size-[16px]">{icon}</div>
        <div className="flex flex-col items-start justify-center leading-[20px] text-nowrap whitespace-pre">
          <p
            className={cn(
              "text-[12px] text-white font-normal",
              isDoneStatus && "text-[#A3A3A3]",
            )}
          >
            {task.title}
          </p>
          {task.notes && (
            <p className="text-[10px] text-[#A3A3A3] font-normal">
              {task.notes}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
