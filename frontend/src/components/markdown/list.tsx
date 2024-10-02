import React from "react";
import { ExtraProps } from "react-markdown";

// Custom component to render <ul> in markdown
export function ul({
  children,
  className,
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps) {
  return (
    <ul className={`list-disc ml-5 pl-2 leading-4 ${className}`}>{children}</ul>
  );
}

// Custom component to render <ol> in markdown
export function ol({
  children,
  className,
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps) {
  return (
    <ol className={`list-decimal ml-5 pl-2 leading-4 ${className}`}>
      {children}
    </ol>
  );
}
