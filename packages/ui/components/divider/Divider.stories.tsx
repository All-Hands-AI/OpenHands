import type { Meta, StoryObj } from "@storybook/react-vite";
import { Divider } from "./Divider";

const meta = {
  title: "Components/Divider",
  component: Divider,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    type: {
      control: {
        type: "select",
      },
      options: ["vertical", "horizontal"],
    },
  },
} satisfies Meta<typeof Divider>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Main: Story = {
  args: {
    type: "vertical",
  },
  render: ({ type }) => (
    <div className="flex justify-center items-center h-64 w-64">
      <Divider type={type} />
    </div>
  ),
};
