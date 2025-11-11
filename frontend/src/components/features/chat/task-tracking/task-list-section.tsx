import { useTranslation } from "react-i18next";
import { TaskItem } from "./task-item";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { I18nKey } from "#/i18n/declaration";

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
    <div className="bg-[#25272d] border border-[#525252] rounded-[12px] w-full">
      <div className="flex flex-col overflow-clip rounded-[inherit]">
        {/* Header Tabs */}
        <div className="border-b border-[#525252] flex h-[41px] items-center px-2 shrink-0">
          <div className="flex gap-1 flex-1 items-center">
            <div className="shrink-0 size-[18px]">
              <LessonPlanIcon className="w-full h-full text-[#9299aa]" />
            </div>
            <div className="flex gap-1 flex-1 items-center">
              <div className="flex flex-col font-medium justify-center text-[11px] text-nowrap text-white tracking-[0.11px]">
                <p className="leading-[16px] whitespace-pre">
                  {t(I18nKey.COMMON$TASKS)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Task Items */}
        <div>
          {taskList.map((task) => (
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      </div>
    </div>
  );
}
