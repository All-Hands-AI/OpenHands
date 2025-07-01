import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "../button/Button";
import { toasterMessages } from "./Toast";

const meta = {
  title: "Components/Toast",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;

const ToastComponent = () => {
  const notify = () => {
    toasterMessages.error("Lorem Ipsum");
    toasterMessages.success("Lorem Ipsum");
    toasterMessages.info("Lorem Ipsum");
    toasterMessages.warning("Lorem Ipsum");
  };

  return (
    <>
      <Button onClick={notify}>Notify</Button>
    </>
  );
};

export const Main: Story = {
  args: {},
  render: ToastComponent,
};
