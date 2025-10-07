export type BaseProps = {
  className?: string;
  testId?: string;
};

export type HTMLProps<T extends React.ElementType> = Omit<
  React.ComponentPropsWithoutRef<T>,
  "children" | "style" | "className"
>;

export type ComponentVariant = "primary" | "secondary" | "tertiary";

export interface IOption<T> {
  label: string;
  value: T;
}
