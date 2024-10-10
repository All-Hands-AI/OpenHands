export function ExternalLink({ children }: React.PropsWithChildren) {
  return (
    <a
      href={children?.toString()}
      target="_blank"
      rel="noreferrer"
      className="underline"
    >
      {children}
    </a>
  );
}
