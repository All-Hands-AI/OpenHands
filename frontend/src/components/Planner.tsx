import React from "react";
import {
  FaCheckCircle,
  FaQuestionCircle,
  FaRegCheckCircle,
  FaRegCircle,
  FaRegClock,
  FaRegTimesCircle,
} from "react-icons/fa";
import { useSelector } from "react-redux";
import { Plan, Task, TaskState } from "../services/planService";
import { RootState } from "../store";

function StatusIcon({ status }: { status: TaskState }): JSX.Element {
  switch (status) {
    case TaskState.OPEN_STATE:
      return <FaRegCircle />;
    case TaskState.COMPLETED_STATE:
      return <FaRegCheckCircle />;
    case TaskState.ABANDONED_STATE:
      return <FaRegTimesCircle />;
    case TaskState.IN_PROGRESS_STATE:
      return <FaRegClock />;
    case TaskState.VERIFIED_STATE:
      return <FaCheckCircle />;
    default:
      return <FaQuestionCircle />;
  }
}

function TaskCard({ task }: { task: Task }): JSX.Element {
  return (
    <div className="flex flex-col rounded bg-neutral-700 p-2 border-neutral-600 border">
      <div className="flex items-center">
        <div className="px-2">
          <StatusIcon status={task.state} />
        </div>
        <div>{task.goal}</div>
      </div>
      {task.subtasks.length > 0 && (
        <div className="flex flex-col gap-2 pt-2">
          {task.subtasks.map((subtask) => (
            <TaskCard key={subtask.id} task={subtask} />
          ))}
        </div>
      )}
    </div>
  );
}

interface PlanProps {
  plan: Plan;
}

function PlanContainer({ plan }: PlanProps): JSX.Element {
  if (plan.mainGoal === undefined) {
    return (
      <div className="p-2">
        Nothing is currently planned. Start a task for this to change.
      </div>
    );
  }
  return (
    <div className="p-2">
      <TaskCard task={plan.task} />
    </div>
  );
}

function Planner(): JSX.Element {
  const plan = useSelector((state: RootState) => state.plan.plan);

  return (
    <div className="h-full w-full bg-neutral-800">
      <PlanContainer plan={plan} />
    </div>
  );
}

export default Planner;
