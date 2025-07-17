import type { Meta, StoryObj } from "@storybook/react-vite";
import { Dialog } from "./Dialog";
import { useState } from "react";
import { Button } from "../button/Button";

const meta = {
  title: "Components/Dialog",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

const DialogComponent = () => {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Button onClick={() => setOpen(true)}>Click to open</Button>
      <Dialog open={open} onOpenChange={setOpen}>
        DialogContent
      </Dialog>
    </div>
  );
};

export const Main: Story = {
  render: ({}) => <DialogComponent />,
};
