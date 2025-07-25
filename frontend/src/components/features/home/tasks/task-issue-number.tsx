import { Typography } from "@openhands/ui";

interface TaskIssueNumberProps {
  issueNumber: number;
  href: string;
}

export function TaskIssueNumber({ href, issueNumber }: TaskIssueNumberProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      data-testid="task-id"
    >
      <Typography.Text className="text-sm text-[#A3A3A3] leading-[16px]">
        #{issueNumber}
      </Typography.Text>
    </a>
  );
}
