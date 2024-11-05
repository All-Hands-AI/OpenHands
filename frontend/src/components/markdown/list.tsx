import React from "react";
import { ExtraProps } from "react-markdown";

// Custom component to render <ul> in markdown
export function ul({
  children,
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps) {
  return <ul className="list-disc ml-5 pl-2 whitespace-normal">{children}</ul>;
}

// Custom component to render <ol> in markdown
export function ol({
  children,
  ordered,
  start,
}: React.ClassAttributes<HTMLElement> &
  React.HTMLAttributes<HTMLElement> &
  ExtraProps & {
    ordered?: boolean;
    start?: number;
  }) {
  return (
    <ol className="ml-5 pl-2 whitespace-normal" style={{ listStyle: 'none' }}>
      {React.Children.map(children, (child, index) => {
        if (React.isValidElement(child)) {
          const originalNumber = child.props?.value || (start || 1) + index;
          return React.cloneElement(child, {
            ...child.props,
            style: { counterReset: `list-item ${originalNumber}` },
            className: 'custom-list-item',
            'data-number': originalNumber,
          });
        }
        return child;
      })}
    </ol>
  );
}
