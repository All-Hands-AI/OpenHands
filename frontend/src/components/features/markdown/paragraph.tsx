import React from "react";
import { ExtraProps } from "react-markdown";

// Custom component to render <p> in markdown with bottom padding
// The last paragraph in a message should not have padding
export function paragraph({
  children,
}: React.ClassAttributes<HTMLParagraphElement> &
  React.HTMLAttributes<HTMLParagraphElement> &
  ExtraProps) {
  // Using Tailwind's last: modifier to remove padding from the last paragraph
  return <p className="pb-[10px] last:pb-0">{children}</p>;
}
