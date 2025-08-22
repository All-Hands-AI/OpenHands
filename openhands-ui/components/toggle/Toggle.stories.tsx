import type { Meta, StoryObj } from "@storybook/react-vite";
import { Toggle, type ToggleProps } from "./Toggle";
import { useState } from "react";

const meta = {
  title: "Components/Toggle",
  component: Toggle,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Toggle>;

export default meta;

type Story = StoryObj<typeof meta>;

const ToggleComponent = (props: ToggleProps) => {
  const [checked, setChecked] = useState(false);
  return (
    <Toggle
      {...props}
      onText="ON"
      offText="OFF"
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
  render: ToggleComponent,
};

export const Disabled: Story = {
  args: {
    disabled: true,
    label:
      "Lorem Ipsum is simply dummy text of the printing and typesetting industry",
  },
  render: ToggleComponent,
};
