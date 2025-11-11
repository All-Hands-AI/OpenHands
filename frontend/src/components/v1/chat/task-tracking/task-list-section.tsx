import { useTranslation } from "react-i18next";
import { TaskItem } from "./task-item";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { TaskItem as TaskItemType } from "#/types/v1/core/base/common";
import { I18nKey } from "#/i18n/declaration";
import { Typography } from "#/ui/typography";

interface TaskListSectionProps {
  taskList: TaskItemType[];
}

export function TaskListSection({ taskList }: TaskListSectionProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-[#25272d] border border-[#525252] rounded-[12px] w-full">
      <div className="flex flex-col overflow-clip">
        {/* Header Tabs */}
        <div className="border-b border-[#525252] flex h-[41px] items-center px-2 shrink-0">
          <div className="flex gap-1 flex-1 items-center">
            <LessonPlanIcon className="shrink-0 w-4.5 h-4.5 text-[#9299aa]" />
            <Typography.Text className="text-[11px] text-nowrap text-white tracking-[0.11px] font-medium leading-[16px] whitespace-pre">
              {t(I18nKey.COMMON$TASKS)}
            </Typography.Text>
          </div>
        </div>

        {/* Task Items */}
        <div>
          {taskList.map((task, index) => (
            <TaskItem key={`task-${index}`} task={task} />
          ))}
        </div>
      </div>
    </div>
  );
}
