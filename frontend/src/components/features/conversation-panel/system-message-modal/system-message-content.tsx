import { Typography } from "#/ui/typography";

interface SystemMessageContentProps {
  content: string;
}

export function SystemMessageContent({ content }: SystemMessageContentProps) {
  return (
    <div className="p-4 shadow-inner">
      <Typography.CodeBlock>{content}</Typography.CodeBlock>
    </div>
  );
}
