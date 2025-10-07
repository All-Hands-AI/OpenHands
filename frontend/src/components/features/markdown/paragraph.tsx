import React from "react";
import { ExtraProps } from "react-markdown";

// Custom component to render <p> in markdown with bottom padding
export function paragraph({
  children,
}: React.ClassAttributes<HTMLParagraphElement> &
  React.HTMLAttributes<HTMLParagraphElement> &
  ExtraProps) {
  return <p className="pb-[10px] last:pb-0">{children}</p>;
}
