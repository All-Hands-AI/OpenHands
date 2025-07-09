import {
  useEffect,
  useId,
  useRef,
  useState,
  type PropsWithChildren,
} from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Icon } from "../icon/Icon";
import { createPortal } from "react-dom";
import {
  FloatingOverlay,
  FloatingPortal,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
  useTransitionStyles,
  useFocus,
} from "@floating-ui/react";
import { FocusTrap } from "focus-trap-react";

export type DialogProps = HTMLProps<"div"> & {
  open: boolean;
  onOpenChange(value: boolean): void;
};

export const Dialog = ({
  open,
  onOpenChange,
  className,
  children,
}: PropsWithChildren<DialogProps>) => {
  const id = useId();

  const { refs, context } = useFloating({
    open,
    onOpenChange,
  });

  const dismiss = useDismiss(context);
  const role = useRole(context);
  const focusTrap = useFocus(context, {});

  const { getFloatingProps } = useInteractions([dismiss, role, focusTrap]);

  const { isMounted, styles } = useTransitionStyles(context, {
    duration: {
      open: 200,
      close: 200,
    },

    initial: {
      opacity: 0,
    },
    open: {
      opacity: 1,
    },
    close: {
      opacity: 0,
    },
  });

  if (!isMounted) {
    return null;
  }

  return (
    <FloatingPortal>
      <FocusTrap>
        <FloatingOverlay
          lockScroll
          className="fixed inset-0 bg-black/50 flex items-center justify-center"
          style={{ opacity: styles.opacity }}
        >
          <div
            ref={refs.setFloating}
            aria-labelledby={`${id}-label`}
            aria-describedby={`${id}-description`}
            {...getFloatingProps()}
            style={styles}
            className={cn(
              "rounded-4xl border-1 border-light-neutral-500 outline-none",
              "transition-all will-change-transform",
              "bg-light-neutral-900 min-w-80 min-h-64 p-6"
            )}
          >
            <div className={cn("text-white", className)}>{children}</div>
            <button
              onClick={() => onOpenChange(false)}
              className="absolute top-4 right-4 cursor-pointer"
            >
              <Icon icon="X" className="w-6 h-6 text-white" />
            </button>
          </div>
        </FloatingOverlay>
      </FocusTrap>
    </FloatingPortal>
  );
};
