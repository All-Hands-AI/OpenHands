import { useTranslation } from "react-i18next";
import { SuggestedTask } from "./task.types";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { cn } from "#/utils/utils";
import { TaskIssueNumber } from "./task-issue-number";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";

const getTaskTypeMap = (
  t: (key: string) => string,
): Record<SuggestedTask["task_type"], string> => ({
  FAILING_CHECKS: t("HOME$FIX_FAILING_CHECKS"),
  MERGE_CONFLICTS: t("HOME$RESOLVE_MERGE_CONFLICTS"),
  OPEN_ISSUE: t("HOME$OPEN_ISSUE"),
  UNRESOLVED_COMMENTS: t("HOME$RESOLVE_UNRESOLVED_COMMENTS"),
});

interface TaskCardProps {
  task: SuggestedTask;
}

export function TaskCard({ task }: TaskCardProps) {
  const { setOptimisticUserMessage } = useOptimisticUserMessage();
  const { mutate: createConversation, isPending } = useCreateConversation();
  const isCreatingConversation = useIsCreatingConversation();
  const { t } = useTranslation();

  const handleLaunchConversation = () => {
    setOptimisticUserMessage(t("TASK$ADDRESSING_TASK"));

    return createConversation({
      repository: {
        name: task.repo,
        gitProvider: task.git_provider,
      },
      suggestedTask: task,
    });
  };

  // Determine the correct URL format based on git provider
  let href: string;
  if (task.git_provider === "gitlab") {
    const issueType =
      task.task_type === "OPEN_ISSUE" ? "issues" : "merge_requests";
    href = `https://gitlab.com/${task.repo}/-/${issueType}/${task.issue_number}`;
  } else if (task.git_provider === "bitbucket") {
    const issueType =
      task.task_type === "OPEN_ISSUE" ? "issues" : "pull-requests";
    href = `https://bitbucket.org/${task.repo}/${issueType}/${task.issue_number}`;
  } else {
    const hrefType = task.task_type === "OPEN_ISSUE" ? "issues" : "pull";
    href = `https://github.com/${task.repo}/${hrefType}/${task.issue_number}`;
  }

  return (
    <li className="py-3 border-b border-[#717888] flex items-center pr-6 last:border-b-0">
      <TaskIssueNumber issueNumber={task.issue_number} href={href} />

      <div className="w-full pl-8">
        <p className="font-semibold">{getTaskTypeMap(t)[task.task_type]}</p>
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
        onClick={handleLaunchConversation}
      >
        {!isPending && t("HOME$LAUNCH")}
        {isPending && t("HOME$LOADING")}
      </button>
    </li>
  );
}
