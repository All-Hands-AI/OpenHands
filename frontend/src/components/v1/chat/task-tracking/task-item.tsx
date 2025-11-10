import { useMemo } from "react";
import { TaskItem as TaskItemType } from "#/types/v1/core/base/common";
import CircleIcon from "#/icons/u-circle.svg?react";

interface TaskItemProps {
  task: TaskItemType;
}

export function TaskItem({ task }: TaskItemProps) {
  const icon = useMemo(() => {
    switch (task.status) {
      // TODO: Add icons for each status
      case "todo":
      case "in_progress":
      case "done":
        return <CircleIcon className="w-4 h-4 text-[#ffffff]" />;
      default:
        return <CircleIcon className="w-4 h-4 text-[#ffffff]" />;
    }
  }, [task.status]);

  return (
    <div className="flex items-center px-4 py-2 w-full" data-name="item">
      <div className="flex gap-[14px] items-center">
        <div className="shrink-0 size-[16px]">{icon}</div>
        <div className="flex flex-col items-start justify-center leading-[20px] pb-[7px] text-nowrap whitespace-pre">
          <p className="text-[12px] text-white font-normal">{task.title}</p>
          {task.notes && (
            <p className="text-[10px] text-neutral-400 font-normal">
              {task.notes}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
