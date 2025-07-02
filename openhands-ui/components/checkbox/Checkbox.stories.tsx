import type { Meta, StoryObj } from "@storybook/react-vite";
import { Checkbox, type CheckboxProps } from "./Checkbox";
import { useState } from "react";

const meta = {
  title: "Components/Checkbox",
  component: Checkbox,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Checkbox>;

export default meta;

type Story = StoryObj<typeof meta>;

const CheckboxComponent = (props: CheckboxProps) => {
  const [checked, setChecked] = useState(false);
  return (
    <Checkbox
      {...props}
      checked={checked}
      onChange={(e) => setChecked(e.target.checked)}
    />
  );
};

export const Enabled: Story = {
  args: {
    label:
      "Lorem Ipsum is simply dummy text of the printing and typesetting industry",
  },
  render: CheckboxComponent,
};

export const Disabled: Story = {
  args: {
    disabled: true,
    label:
      "Lorem Ipsum is simply dummy text of the printing and typesetting industry",
  },
  render: CheckboxComponent,
};
