import type { Meta, StoryObj } from "@storybook/react-vite";
import { Input, type InputProps } from "./Input";
import { useState } from "react";
import { Icon } from "../icon/Icon";

const meta = {
  title: "Components/Input",
  component: Input,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Input>;

export default meta;

type Story = StoryObj<typeof meta>;

const InputComponent = (props: InputProps) => {
  const [value, setValue] = useState("");
  return (
    <Input
      {...props}
      value={value}
      start={<Icon icon="HeartFill" />}
      end={<Icon icon="Heart" />}
      placeholder="abc"
      onChange={(e) => setValue(e.target.value)}
    />
  );
};

export const Enabled: Story = {
  args: {
    label: "Lorem Ipsum",
    hint: "Hint",
  },

  render: InputComponent,
};
export const Error: Story = {
  args: {
    label: "Lorem Ipsum",
    error: "Error",
  },

  render: InputComponent,
};
export const ReadOnly: Story = {
  args: {
    label: "Lorem Ipsum",
    readOnly: true,
  },

  render: InputComponent,
};

export const Disabled: Story = {
  args: {
    disabled: true,
    label:
      "Lorem Ipsum is simply dummy text of the printing and typesetting industry",
  },
  render: InputComponent,
};
