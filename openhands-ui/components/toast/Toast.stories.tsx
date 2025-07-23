import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "../button/Button";
import { toasterMessages } from "./Toast";
import { ToastManager } from "./ToastManager";

const meta = {
  title: "Components/Toast",
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta;

export default meta;

type Story = StoryObj<typeof meta>;
type ToastType = keyof typeof toasterMessages;

const toastComponents: Record<ToastType, (text?: string) => void> = {
  error: toasterMessages.error,
  success: toasterMessages.success,
  info: toasterMessages.info,
  warning: toasterMessages.warning,
};

const ToastComponent = () => {
  return (
    <ToastManager>
      <div className="flex flex-col gap-y-4">
        <Button onClick={() => toastComponents["error"]("Lorem Ipsum")}>
          Show error toast
        </Button>
        <Button onClick={() => toastComponents["info"]("Lorem Ipsum")}>
          Show info toast
        </Button>
        <Button onClick={() => toastComponents["success"]("Lorem Ipsum")}>
          Show success toast
        </Button>
        <Button onClick={() => toastComponents["warning"]("Lorem Ipsum")}>
          Show warning toast
        </Button>
      </div>
    </ToastManager>
  );
};

export const Main: Story = {
  args: {},
  render: () => <ToastComponent />,
};
