interface HelpLinkProps {
  testId: string;
  text: string;
  linkText: string;
  href: string;
  suffix?: string;
}

export function HelpLink({
  testId,
  text,
  linkText,
  href,
  suffix,
}: HelpLinkProps) {
  return (
    <p data-testid={testId} className="text-xs">
      {text}{" "}
      <a
        href={href}
        rel="noreferrer noopener"
        target="_blank"
        className="underline underline-offset-2"
      >
        {linkText}
      </a>
      {suffix && ` ${suffix}`}
    </p>
  );
}
