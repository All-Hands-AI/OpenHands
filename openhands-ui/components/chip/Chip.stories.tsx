import type { Meta, StoryObj } from "@storybook/react-vite";
import { Chip, type ChipProps } from "./Chip";

const colors = ["primaryDark", "primaryLight", "green", "red", "aqua", "gray"];

const meta = {
  title: "Components/Chip",
  component: Chip,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    color: {
      control: {
        type: "select",
      },
      options: colors,
    },
  },
} satisfies Meta<typeof Chip>;

export default meta;

type Story = StoryObj<typeof meta>;

const ChipComponent = (props: ChipProps) => {
  return <Chip {...props}>Hello</Chip>;
};

export const Main: Story = {
  args: {
    color: "aqua",
    variant: "pill",
  },
  render: ChipComponent,
};
