export type BaseProps = {
  className?: string;
  style?: React.CSSProperties;
  testId?: string;
};

export type HTMLProps<T extends React.ElementType> = Omit<
  React.ComponentPropsWithoutRef<T>,
  "children"
>;

export type ComponentVariant = "primary" | "secondary" | "tertiary";

export interface IOption<T> {
  label: string;
  value: T;
}
