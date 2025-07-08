import { Typography } from "../Typography";
import type { Meta, StoryObj } from "@storybook/react";

const meta: Meta = {
  title: "Components/Typography",
  parameters: {
    layout: "centered",
  },
  argTypes: {
    fontSize: {
      control: {
        type: "select",
      },
      options: ["xxs", "xs", "s", "m", "l", "xl"],
    },
    fontWeight: {
      control: {
        type: "select",
      },
      options: [100, 200, 300, 400, 500, 600, 700, 800, 900],
    },
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Other: Story = {
  args: {
    fontSize: "m",
  },
  render: ({ fontSize, fontWeight }) => (
    <div className="flex flex-col gap-y-2">
      <Typography.Text fontSize={fontSize} fontWeight={fontWeight}>
        Text
      </Typography.Text>
      <Typography.Code fontSize={fontSize} fontWeight={fontWeight}>
        Code
      </Typography.Code>
    </div>
  ),
};
