import React from "react";
import { useSelector } from "react-redux";
import { Plan, Task } from "../services/planService";
import { RootState } from "../store";

interface TaskProps {
  task: Task;
}

function TaskCard({ task }: TaskProps): JSX.Element {
  return (
    <div className="flex flex-col rounded bg-neutral-400 p-2">
      <div className="flex">
        <div className="pr-4">{task.state}</div>
        <div>{task.goal}</div>
      </div>
      <div>
        {task.subtasks.map((subtask) => (
          <TaskCard key={subtask.id} task={subtask} />
        ))}
      </div>
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
    <div className="h-full w-full bg-neutral-700">
      <PlanContainer plan={plan} />
    </div>
  );
}

export default Planner;
