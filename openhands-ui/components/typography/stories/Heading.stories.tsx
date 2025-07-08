import { Typography } from "../Typography";
import type { Meta, StoryObj } from "@storybook/react";

const meta: Meta = {
  title: "Components/Typography",
  parameters: {
    layout: "centered",
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Headings: Story = {
  render: () => (
    <div className="flex flex-col gap-y-2">
      <Typography.H1 className="text-white">Heading 1</Typography.H1>
      <Typography.H2>Heading 2</Typography.H2>
      <Typography.H3>Heading 3</Typography.H3>
      <Typography.H4>Heading 4</Typography.H4>
      <Typography.H5>Heading 5</Typography.H5>
      <Typography.H6>Heading 6</Typography.H6>
    </div>
  ),
};
