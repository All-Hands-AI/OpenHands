import { Bold } from "./bold";

interface SectionProps {
  title: string;
}

export function Section({
  children,
  title,
}: React.PropsWithChildren<SectionProps>) {
  return (
    <section className="flex flex-col gap-5">
      <Bold underline>{title}</Bold>
      <article className="flex flex-col gap-2">{children}</article>
    </section>
  );
}
