import { toast as sonnerToast, type ExternalToast } from "sonner";
import { Icon, type IconProps } from "../icon/Icon";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";
import { toastStyles } from "./utils";
import type { JSX } from "react";
import { invariant } from "../../shared/utils/invariant";
import type { BaseProps } from "../../shared/types";

type RenderContentProps = {
  onDismiss: () => void;
};

type WithRenderContent = {
  renderContent: (props: RenderContentProps) => JSX.Element;
  text?: never;
  icon?: never;
};

type WithTextAndIcon = {
  text: string;
  icon: IconProps["icon"];
  iconClassName: string;
  renderContent?: never;
};

type IBaseToastProps = (WithRenderContent | WithTextAndIcon) & {
  id: string | number;
};
const BaseToast = (props: IBaseToastProps) => {
  invariant(
    !!props.renderContent || !!props.text,
    "Either define renderContent or text. Both cannot be defined."
  );

  const onDismiss = () => sonnerToast.dismiss(props.id);

  return (
    <div
      className={cn(
        "border-1 border-light-neutral-500 rounded-l-[100px] rounded-r-4xl",
        "bg-light-neutral-900 px-3 py-3",
        "max-w-sm min-w-32",
        "flex flex-row items-center justify-between gap-x-4"
      )}
    >
      {props.renderContent ? (
        props.renderContent({ onDismiss })
      ) : (
        <>
          <Icon
            icon={props.icon}
            className={cn("w-6 h-6 flex-shrink-0", props.iconClassName)}
          />
          <Typography.Text fontSize="xs" className="text-white">
            {props.text}
          </Typography.Text>
          <button onClick={onDismiss} className="cursor-pointer">
            <Icon icon="X" className={cn("w-6 h-6 flex-shrink-0 text-white")} />
          </button>
        </>
      )}
    </div>
  );
};

export const toasterMessages = {
  error: (text?: string, props?: ExternalToast) => {
    const styles = toastStyles["error"];
    sonnerToast.custom(
      (id) => (
        <BaseToast
          id={id}
          icon={styles.icon}
          iconClassName={cn(styles.iconColor)}
          text={text!}
        />
      ),
      props
    );
  },
  success: (text?: string, props?: ExternalToast) => {
    const styles = toastStyles["success"];
    sonnerToast.custom(
      (id) => (
        <BaseToast
          id={id}
          icon={styles.icon}
          iconClassName={cn(styles.iconColor)}
          text={text!}
        />
      ),
      props
    );
  },
  info: (text?: string, props?: ExternalToast) => {
    const styles = toastStyles["info"];
    sonnerToast.custom(
      (id) => (
        <BaseToast
          id={id}
          icon={styles.icon}
          iconClassName={cn(styles.iconColor)}
          text={text!}
        />
      ),
      props
    );
  },
  warning: (text?: string, props?: ExternalToast) => {
    const styles = toastStyles["warning"];
    sonnerToast.custom(
      (id) => (
        <BaseToast
          id={id}
          icon={styles.icon}
          iconClassName={cn(styles.iconColor)}
          text={text!}
        />
      ),
      props
    );
  },
  custom: (
    renderContent: WithRenderContent["renderContent"],
    props?: ExternalToast
  ) => {
    sonnerToast.custom(
      (id) => <BaseToast id={id} renderContent={renderContent} />,
      props
    );
  },
};
