import { type PropsWithChildren } from "react";
import { Toaster, type ToasterProps } from "sonner";

export const ToastManager = (props: PropsWithChildren<ToasterProps>) => {
  return (
    <>
      <Toaster {...props} />
      {props.children}
    </>
  );
};
