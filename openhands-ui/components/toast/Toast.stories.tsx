import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "../button/Button";
import { ToastManager } from "./ToastManager";
import { toasterMessages } from "./Toast";
import React from "react";

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

const ToastComponent = ({ type }: { type: ToastType }) => {
  return (
    <ToastManager>
      <Button onClick={() => toastComponents[type]("Lorem Ipsum")}>
        Notify
      </Button>
    </ToastManager>
  );
};

export const Success: Story = {
  args: {},
  render: () => <ToastComponent type={"success"} />,
};

export const Error: Story = {
  args: {},
  render: () => <ToastComponent type={"error"} />,
};

export const Info: Story = {
  args: {},
  render: () => <ToastComponent type={"info"} />,
};

export const Warning: Story = {
  args: {},
  render: () => <ToastComponent type={"warning"} />,
};
