import { useTranslation } from "react-i18next";
import { SuggestedTask } from "./task.types";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { cn } from "#/utils/utils";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { TaskIssueNumber } from "./task-issue-number";
import { Provider } from "#/types/settings";
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
  const { data: repositories } = useUserRepositories();
  const { mutate: createConversation, isPending } = useCreateConversation();
  const isCreatingConversation = useIsCreatingConversation();
  const { t } = useTranslation();

  const getRepo = (repo: string, git_provider: Provider) => {
    const selectedRepo = repositories?.find(
      (repository) =>
        repository.full_name === repo &&
        repository.git_provider === git_provider,
    );

    return selectedRepo;
  };

  const handleLaunchConversation = () => {
    const repo = getRepo(task.repo, task.git_provider);
    setOptimisticUserMessage(t("TASK$ADDRESSING_TASK"));

    return createConversation({
      selectedRepository: repo,
      suggested_task: task,
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
    <li className="py-3 border-b border-[#717888] flex items-center pr-6">
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
