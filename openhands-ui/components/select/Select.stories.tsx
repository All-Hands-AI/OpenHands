import type { Meta, StoryObj } from "@storybook/react-vite";
import { Select, type SelectProps } from "./Select";
import type { IOption } from "../../shared/types";
import { useState } from "react";

const meta = {
  title: "Components/Select",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

const options = [
  { label: "Red", value: "red" },
  { label: "Green", value: "green" },
  { label: "Blue", value: "blue" },
  { label: "Yellow", value: "yellow" },
  { label: "Purple", value: "purple" },
  { label: "Orange", value: "orange" },
  { label: "Black", value: "black" },
  { label: "White", value: "white" },
  { label: "Gray", value: "gray" },
  { label: "Pink", value: "pink" },
];

const SelectComponent = (props: Partial<SelectProps<unknown>>) => {
  const [value, setValue] = useState<IOption<string> | null>(
    (props.value as IOption<string>) ?? null
  );
  return (
    <div className="min-w-104">
      <Select
        {...props}
        label="Select label"
        value={value}
        onChange={setValue}
        placeholder="Select an option"
        options={options}
        className="h-64 max-w-128 p-4"
      />
    </div>
  );
};

export const Main: Story = {
  args: {},
  render: ({}) => <SelectComponent />,
};

export const Error: Story = {
  args: {},
  render: ({}) => <SelectComponent error="This field is required" />,
};
export const Hint: Story = {
  args: {},
  render: ({}) => <SelectComponent hint="This is hint" />,
};

export const Disabled: Story = {
  args: {},
  render: ({}) => <SelectComponent disabled value={options[1]} />,
};

export const ReadOnly: Story = {
  args: {},
  render: ({}) => <SelectComponent readOnly value={options[0]} />,
};
