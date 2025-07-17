import type { Meta, StoryObj } from "@storybook/react-vite";
import { InteractiveChip, type InteractiveChipProps } from "./InteractiveChip";
import { Icon } from "../icon/Icon";

const meta = {
  title: "Components/InteractiveChip",
  component: InteractiveChip,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof InteractiveChip>;

export default meta;

type Story = StoryObj<typeof meta>;

const InteractiveChipComponent = (props: InteractiveChipProps) => {
  return (
    <InteractiveChip
      {...props}
      start={<Icon icon="Check" />}
      end={<Icon icon="X" />}
    >
      Click me
    </InteractiveChip>
  );
};

export const Elevated: Story = {
  args: {
    type: "elevated",
    disabled: false,
  },
  render: InteractiveChipComponent,
};

export const Filled: Story = {
  args: {
    type: "filled",
    disabled: false,
  },
  render: InteractiveChipComponent,
};
