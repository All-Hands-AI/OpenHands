import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button } from "./Button";
import { Icon } from "../icon/Icon";

const meta = {
  title: "Components/Button",
  component: Button,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {},
} satisfies Meta<typeof Button>;

export default meta;

type Story = StoryObj<typeof meta>;

const WithIconsComponent = () => {
  return (
    <div className="flex flex-col gap-y-2">
      <Button
        variant="primary"
        size="small"
        lead={<Icon icon="ChevronLeft" />}
        trail={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
      <Button
        variant="secondary"
        size="small"
        lead={<Icon icon="ChevronLeft" />}
        trail={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>

      <Button
        variant="tertiary"
        size="small"
        lead={<Icon icon="ChevronLeft" />}
        trail={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
    </div>
  );
};
const LargeComponent = () => {
  return (
    <div className="flex flex-col gap-y-2">
      <Button
        variant="primary"
        size="large"
        lead={<Icon icon="ChevronLeft" />}
        trail={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
      <Button
        variant="secondary"
        size="large"
        lead={<Icon icon="HeartFill" />}
        trail={<Icon icon="HeartFill" />}
      >
        Click me
      </Button>

      <Button
        variant="tertiary"
        size="large"
        lead={<Icon icon="HeartFill" />}
        trail={<Icon icon="HeartFill" />}
      >
        Click me
      </Button>
    </div>
  );
};

export const Primary: Story = {
  args: {
    variant: "primary",
    children: "Click me",
  },
};
export const Secondary: Story = {
  args: {
    variant: "secondary",
    children: "Click me",
  },
};
export const Tertiary: Story = {
  args: {
    variant: "tertiary",
    children: "Click me",
  },
};
export const Large: Story = {
  args: {
    size: "large",
    children: "Click me",
  },
  render: LargeComponent,
};

export const WithIcons: Story = {
  args: {
    variant: "primary",
    children: "Click me",
  },
  render: WithIconsComponent,
};
