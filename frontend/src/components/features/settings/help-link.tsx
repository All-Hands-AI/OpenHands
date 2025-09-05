import { cn } from "#/utils/utils";

interface HelpLinkProps {
  testId: string;
  text: string;
  linkText: string;
  href: string;
  suffix?: string;
  className?: string;
  linkTextClassName?: string;
  suffixClassName?: string;
}

export function HelpLink({
  testId,
  text,
  linkText,
  href,
  suffix,
  className,
  linkTextClassName,
  suffixClassName,
}: HelpLinkProps) {
  return (
    <p data-testid={testId} className={cn("text-xs", className)}>
      {text}{" "}
      <a
        href={href}
        rel="noreferrer noopener"
        target="_blank"
        className={cn("underline underline-offset-2", linkTextClassName)}
      >
        {linkText}
      </a>
      {suffix && <span className={suffixClassName}>{suffix}</span>}
    </p>
  );
}
