import React from "react";
import { ExtraProps } from "react-markdown";

// Custom component to render <ul> in markdown
export function ul({
  children,
}: React.ClassAttributes<HTMLUListElement> &
  React.HTMLAttributes<HTMLUListElement> &
  ExtraProps) {
  return <ul className="list-disc ml-5 pl-2 whitespace-normal">{children}</ul>;
}

// Custom component to render <ol> in markdown
export function ol({
  children,
  start,
}: React.ClassAttributes<HTMLOListElement> &
  React.OlHTMLAttributes<HTMLOListElement> &
  ExtraProps) {
  return (
    <ol className="list-decimal ml-5 pl-2 whitespace-normal" start={start}>
      {children}
    </ol>
  );
}
