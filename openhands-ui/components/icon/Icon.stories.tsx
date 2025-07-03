import type { Meta, StoryObj } from "@storybook/react-vite";
import { Icon } from "./Icon";
import * as icons from "react-bootstrap-icons";
import { Typography } from "../typography/Typography";

const iconNames = Object.keys(icons);

const IconComponent = () => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
      {iconNames.map((icon) => (
        <div key={icon} className="flex flex-col gap-y-1 items-center">
          <Icon icon={icon as any} className="w-6 h-6 text-white" />
          <Typography.Text fontSize="xs" className="text-white">
            {icon}
          </Typography.Text>
        </div>
      ))}
    </div>
  );
};

const meta = {
  title: "Components/Icon",
  component: IconComponent,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

export const Main: Story = {
  render: IconComponent,
};
