import type { Meta, StoryObj } from "@storybook/react-vite";
import { RadioGroup, type RadioGroupProps } from "./RadioGroup";
import { useState } from "react";
import type { IOption } from "../../shared/types";

type RadioGroupComponentProps<T extends string> = Omit<
  RadioGroupProps<T>,
  "value" | "onChange"
>;

const RadioGroupComponent = <T extends string>(
  props: RadioGroupComponentProps<T>
) => {
  const [value, setValue] = useState(props.options[0]!.value);
  return (
    <RadioGroup {...props} value={value} onChange={(o) => setValue(o.value)} />
  );
};
const meta = {
  title: "Components/RadioGroup",
  component: RadioGroupComponent,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof RadioGroupComponent>;

export default meta;

type Story = StoryObj<typeof meta>;

const options: IOption<string>[] = [
  { label: "Red", value: "red" },
  { label: "Blue", value: "blue" },
  { label: "Green", value: "green" },
  { label: "Primary", value: "primary" },
  { label: "Purple", value: "purple" },
];

export const Enabled: Story = {
  args: {
    options,
  },
  render: RadioGroupComponent,
};

export const Disabled: Story = {
  args: {
    disabled: true,
    options,
  },
  render: RadioGroupComponent,
};
