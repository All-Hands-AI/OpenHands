import {
  useFloating,
  offset,
  flip,
  shift,
  useHover,
  useFocus,
  useRole,
  useDismiss,
  useInteractions,
  FloatingPortal,
  autoUpdate,
  arrow,
  FloatingArrow,
  type UseFloatingOptions,
  useClick,
} from "@floating-ui/react";
import { useRef, useState, type PropsWithChildren } from "react";
import { Typography } from "../typography/Typography";

type ControlledTooltipProps = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
};

type UncontrolledTooltipProps = {
  open?: undefined;
  setOpen?: undefined;
};

type TooltipTriggerType = "click" | "hover";

type BaseTooltipProps = {
  text: string;
  withArrow?: boolean;
  className?: string;
  placement?: UseFloatingOptions["placement"];
  trigger?: TooltipTriggerType;
};

export type TooltipProps = BaseTooltipProps &
  (ControlledTooltipProps | UncontrolledTooltipProps);

export const Tooltip = ({
  children,
  className,
  text,
  withArrow = true,
  placement = "top",
  open,
  setOpen: setOpenProp,
  trigger = "hover",
}: PropsWithChildren<TooltipProps>) => {
  const [localOpen, setLocalOpen] = useState(false);
  const arrowRef = useRef(null);
  const readOnlyTrigger = useRef(trigger);

  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : localOpen;
  const setOpen = isControlled ? setOpenProp : setLocalOpen;

  const { refs, floatingStyles, context } = useFloating({
    open: isOpen,
    onOpenChange: setOpen,
    middleware: [
      offset(8),
      flip(),
      shift(),
      withArrow
        ? arrow({
            element: arrowRef,
          })
        : undefined,
    ],
    whileElementsMounted: autoUpdate,
    placement,
  });

  const triggerInteractions =
    readOnlyTrigger.current === "click"
      ? [useClick(context)]
      : [useHover(context, { move: false }), useFocus(context)];

  const dismiss = useDismiss(context);
  const role = useRole(context, { role: "tooltip" });

  const { getReferenceProps, getFloatingProps } = useInteractions([
    ...triggerInteractions,
    dismiss,
    role,
  ]);
  return (
    <>
      <button
        ref={refs.setReference}
        {...getReferenceProps()}
        className={className}
      >
        {children}
      </button>
      {isOpen && (
        <FloatingPortal>
          <div
            ref={refs.setFloating}
            style={floatingStyles}
            {...getFloatingProps()}
            className="bg-light-neutral-300 px-3 py-2 rounded-lg z-50 max-w-52"
          >
            <Typography.Text
              fontSize="s"
              fontWeight={500}
              className="text-grey-985"
            >
              {text}
            </Typography.Text>
            {withArrow && (
              <FloatingArrow
                ref={arrowRef}
                context={context}
                tipRadius={3}
                height={8}
                width={12}
                fill="var(--color-light-neutral-300)"
              />
            )}
          </div>
        </FloatingPortal>
      )}
    </>
  );
};
