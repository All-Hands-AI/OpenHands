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

export const Indeterminate: Story = {
  render: () => <Spinner />,
};
