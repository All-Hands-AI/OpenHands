import { SuggestedTask } from "./task.types";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { cn } from "#/utils/utils";

interface TaskCardProps {
  task: SuggestedTask;
}

export function TaskCard({ task }: TaskCardProps) {
  const { mutate: createConversation, isPending } = useCreateConversation();
  const isCreatingConversation = useIsCreatingConversation();

  return (
    <li className="py-3 border-b border-[#717888] flex items-center pr-6">
      <span data-testid="task-id">#{task.issue_number}</span>

      <div className="w-full pl-8">
        <p className="font-semibold">{task.task_type}</p>
        <p>{task.title}</p>
      </div>

      <button
        type="button"
        data-testid="task-launch-button"
        className={cn(
          "underline underline-offset-2 disabled:opacity-80",
          isPending && "no-underline font-bold",
        )}
        disabled={isCreatingConversation}
        onClick={() => createConversation({})}
      >
        {!isPending && "Launch"}
        {isPending && "Loading..."}
      </button>
    </li>
  );
}
