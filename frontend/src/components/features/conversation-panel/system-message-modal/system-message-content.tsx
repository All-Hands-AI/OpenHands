import { Typography } from "#/ui/typography";

interface SystemMessageContentProps {
  content: string;
}

export function SystemMessageContent({ content }: SystemMessageContentProps) {
  return (
    <Typography.Text className="p-4 whitespace-pre-wrap font-mono text-sm leading-relaxed text-gray-300 shadow-inner">
      {content}
    </Typography.Text>
  );
}
