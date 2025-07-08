import type { Meta, StoryObj } from "@storybook/react-vite";

import { Button, type ButtonProps } from "./Button";
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

const WithIconsComponent = (props: ButtonProps) => {
  return (
    <div className="flex flex-col gap-y-2">
      <Button
        variant="primary"
        size="small"
        {...props}
        start={<Icon icon="ChevronLeft" />}
        end={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
      <Button
        variant="secondary"
        size="small"
        {...props}
        start={<Icon icon="ChevronLeft" />}
        end={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>

      <Button
        variant="tertiary"
        size="small"
        {...props}
        start={<Icon icon="ChevronLeft" />}
        end={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
    </div>
  );
};
const LargeComponent = (props: ButtonProps) => {
  return (
    <div className="flex flex-col gap-y-2">
      <Button
        variant="primary"
        size="large"
        {...props}
        start={<Icon icon="ChevronLeft" />}
        end={<Icon icon="ChevronRight" />}
      >
        Click me
      </Button>
      <Button
        variant="secondary"
        size="large"
        {...props}
        start={<Icon icon="HeartFill" />}
        end={<Icon icon="HeartFill" />}
      >
        Click me
      </Button>

      <Button
        variant="tertiary"
        size="large"
        {...props}
        start={<Icon icon="HeartFill" />}
        end={<Icon icon="HeartFill" />}
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
    disabled: false,
  },
};
export const Secondary: Story = {
  args: {
    variant: "secondary",
    children: "Click me",
    disabled: false,
  },
};
export const Tertiary: Story = {
  args: {
    variant: "tertiary",
    children: "Click me",
    disabled: false,
  },
};
export const Large: Story = {
  args: {
    disabled: false,
  },
  render: LargeComponent,
};

export const WithIcons: Story = {
  args: {
    disabled: false,
  },
  render: WithIconsComponent,
};
