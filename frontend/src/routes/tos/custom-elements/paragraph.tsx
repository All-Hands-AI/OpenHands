import { cn } from "#/utils/utils";

interface ParagraphProps {
  bold?: boolean;
  italic?: boolean;
}

export function Paragraph({
  children,
  bold,
  italic,
}: React.PropsWithChildren<ParagraphProps>) {
  return (
    <p className={cn(bold && "font-bold", italic && "italic")}>{children}</p>
  );
}
