import type { Meta, StoryObj } from "@storybook/react-vite";
import { Tooltip } from "./Tooltip";
import { Typography } from "../typography/Typography";

const meta = {
  title: "Components/Tooltip",
  component: Tooltip,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    placement: {
      control: {
        type: "select",
      },
      options: ["top", "right", "bottom", "left"],
    },
  },
} satisfies Meta<typeof Tooltip>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Hover: Story = {
  args: {
    placement: "top",
    text: "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries",
    withArrow: true,
  },
  render: ({ text, withArrow, placement }) => (
    <Tooltip
      text={text}
      withArrow={withArrow}
      placement={placement}
      trigger="hover"
    >
      <Typography.Text>Hover me</Typography.Text>
    </Tooltip>
  ),
};
export const Click: Story = {
  args: {
    placement: "top",
    text: "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries",
    withArrow: true,
  },
  render: ({ text, withArrow, placement }) => (
    <Tooltip
      text={text}
      withArrow={withArrow}
      placement={placement}
      trigger="click"
    >
      <Typography.Text>Click me</Typography.Text>
    </Tooltip>
  ),
};
