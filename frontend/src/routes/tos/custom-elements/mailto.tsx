export function Mailto({ children }: React.PropsWithChildren) {
  return (
    <a href={`mailto:${children?.toString()}`} className="underline">
      {children}
    </a>
  );
}
