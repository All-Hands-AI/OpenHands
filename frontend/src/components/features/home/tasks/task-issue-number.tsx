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
      #<span className="underline underline-offset-2">{issueNumber}</span>
    </a>
  );
}
