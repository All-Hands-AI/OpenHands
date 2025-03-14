interface HelpLinkProps {
  testId: string;
  text: string;
  links: Array<{
    text: string;
    href: string;
  }>;
}

export function HelpLink({ testId, text, links }: HelpLinkProps) {
  return (
    <p data-testid={testId} className="text-xs">
      {text}{" "}
      {links.map((link, index) => (
        <>
          {index > 0 && " or "}
          <a
            key={link.href}
            href={link.href}
            rel="noreferrer noopener"
            target="_blank"
            className="underline underline-offset-2"
          >
            {link.text}
          </a>
        </>
      ))}
      .
    </p>
  );
}
