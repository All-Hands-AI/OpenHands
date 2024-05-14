import React from "react";
import { useTranslation } from "react-i18next";
import {
  FaCheckCircle,
  FaQuestionCircle,
  FaRegCheckCircle,
  FaRegCircle,
  FaRegClock,
  FaRegTimesCircle,
} from "react-icons/fa";
import { VscListOrdered } from "react-icons/vsc";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { Task, TaskState } from "#/services/taskService";
import { RootState } from "#/store";

function StatusIcon({ status }: { status: TaskState }): JSX.Element {
  switch (status) {
    case TaskState.OPEN_STATE:
      return <FaRegCircle />;
    case TaskState.COMPLETED_STATE:
      return <FaRegCheckCircle className="text-green-200" />;
    case TaskState.ABANDONED_STATE:
      return <FaRegTimesCircle className="text-red-200" />;
    case TaskState.IN_PROGRESS_STATE:
      return <FaRegClock className="text-yellow-200" />;
    case TaskState.VERIFIED_STATE:
      return <FaCheckCircle className="text-green-200" />;
    default:
      return <FaQuestionCircle />;
  }
}

function TaskCard({ task, level }: { task: Task; level: number }): JSX.Element {
  return (
    <div
      className={`flex flex-col rounded-r bg-neutral-700 p-2 border-neutral-600 ${level < 2 ? "border-l-3" : ""}`}
    >
      <div className="flex items-center">
        <div className="px-2">
          <StatusIcon status={task.state} />
        </div>
        <div>{task.goal}</div>
      </div>
      {task.subtasks.length > 0 && (
        <div className="flex flex-col pt-2 pl-2">
          {task.subtasks.map((subtask) => (
            <TaskCard key={subtask.id} task={subtask} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function Planner(): JSX.Element {
  const { t } = useTranslation();
  const task = useSelector((state: RootState) => state.task.task);

  if (!task || !task.subtasks?.length) {
    return (
      <div className="w-full h-full flex flex-col text-neutral-400 items-center justify-center">
        <VscListOrdered size={100} />
        {t(I18nKey.PLANNER$EMPTY_MESSAGE)}
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-neutral-800">
      <div className="p-2 overflow-y-auto h-full flex flex-col gap-2">
        {task.subtasks.map((subtask) => (
          <TaskCard key={subtask.id} task={subtask} level={0} />
        ))}
      </div>
    </div>
  );
}

export default Planner;
