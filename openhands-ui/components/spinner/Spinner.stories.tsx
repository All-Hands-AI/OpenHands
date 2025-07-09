import type { Meta, StoryObj } from "@storybook/react-vite";
import { Spinner } from "./Spinner";
import { useEffect, useState } from "react";

const meta = {
  title: "Components/Spinner",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

const DeterminateSpinner = () => {
  const [percentage, setPercentage] = useState(10);

  useEffect(() => {
    setTimeout(() => setPercentage(Math.min(100, percentage + 30)), 600);
  }, [percentage]);
  return <Spinner determinate value={percentage} />;
};

export const Determinate: Story = {
  render: () => <DeterminateSpinner />,
};

export const IndeterminateSimple: Story = {
  render: () => <Spinner variant="simple" />,
  name: "Indeterminate (Simple)",
};

export const IndeterminateDynamic: Story = {
  render: () => <Spinner variant="dynamic" />,
  name: "Indeterminate (Dynamic)",
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4 items-center">
      <div className="flex gap-4 items-center">
        <Spinner variant="simple" />
        <span>Simple Indeterminate</span>
      </div>
      <div className="flex gap-4 items-center">
        <Spinner variant="dynamic" />
        <span>Dynamic Indeterminate</span>
      </div>
      <div className="flex gap-4 items-center">
        <DeterminateSpinner />
        <span>Determinate</span>
      </div>
    </div>
  ),
};
