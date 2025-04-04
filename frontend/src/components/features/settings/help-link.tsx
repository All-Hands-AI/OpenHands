import { cn } from "#/utils/utils";

interface HelpLinkProps {
  testId: string;
  text: string;
  linkText: string;
  href: string;
  classNames?: {
    text?: string;
    linkText?: string;
  };
}

export function HelpLink({
  testId,
  text,
  linkText,
  href,
  classNames,
}: HelpLinkProps) {
  return (
    <p data-testid={testId} className={cn("text-xs", classNames?.text)}>
      {text}{" "}
      <a
        href={href}
        rel="noreferrer noopener"
        target="_blank"
        className={cn("underline underline-offset-2", classNames?.linkText)}
      >
        {linkText}
      </a>
    </p>
  );
}
