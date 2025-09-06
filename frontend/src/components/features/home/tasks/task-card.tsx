import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { SuggestedTask } from "#/utils/types";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { TaskIssueNumber } from "./task-issue-number";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { cn } from "#/utils/utils";

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
  const { mutate: createConversation } = useCreateConversation();
  const isCreatingConversation = useIsCreatingConversation();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleLaunchConversation = () => {
    setOptimisticUserMessage(t("TASK$ADDRESSING_TASK"));

    return createConversation(
      {
        repository: {
          name: task.repo,
          gitProvider: task.git_provider,
        },
        suggestedTask: task,
      },
      {
        onSuccess: (data) => {
          navigate(`/conversations/${data.conversation_id}`);
        },
      },
    );
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
    <button
      type="button"
      data-testid="task-launch-button"
      className={cn(
        "w-full p-[14px] text-left flex items-center justify-between cursor-pointer hover:bg-[#5C5D62] transition-all duration-300 rounded-lg",
        isCreatingConversation && "cursor-not-allowed",
      )}
      disabled={isCreatingConversation}
      onClick={handleLaunchConversation}
    >
      <div className="flex items-center gap-3 min-w-0 w-full">
        <TaskIssueNumber issueNumber={task.issue_number} href={href} />

        <div className="flex flex-col gap-1 min-w-0 flex-1">
          <span className="text-xs text-white leading-6 font-normal truncate">
            {getTaskTypeMap(t)[task.task_type]}
          </span>
          <span
            className="text-xs text-[#A3A3A3] leading-4 font-normal max-w-70 truncate"
            title={task.title}
          >
            {task.title}
          </span>
        </div>
      </div>
    </button>
  );
}
