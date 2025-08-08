import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "../button/Button";
import { toasterMessages } from "./Toast";
import { ToastManager } from "./ToastManager";
import { Typography } from "../typography/Typography";

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
  custom: (text) => toasterMessages.custom(() => <div>{text}</div>),
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
        <Button onClick={() => toastComponents["custom"]("Lorem Ipsum")}>
          Show custom toast
        </Button>
      </div>
    </ToastManager>
  );
};
const CustomToastComponent = () => {
  const notify = () => {
    toasterMessages.custom((props) => (
      <Typography.Text fontSize="xs" className="text-white">
        Custom toast !
      </Typography.Text>
    ));
  };

  return (
    <>
      <ToastManager>
        <Button onClick={notify}>Notify</Button>
      </ToastManager>
    </>
  );
};

export const Main: Story = {
  args: {},
  render: () => <ToastComponent />,
};
export const Custom: Story = {
  args: {},
  render: CustomToastComponent,
};
