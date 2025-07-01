import { toast } from "react-toastify";
import { Icon, type IconProps } from "../icon/Icon";
import { toastStyles } from "./utils";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";

type IBaseToastProps = {
  text: string;
  icon: IconProps["icon"];
  iconClassName: string;
  closeToast?: () => void;
};
const BaseToast = (props: IBaseToastProps) => {
  return (
    <div
      className={cn(
        "border-1 border-light-neutral-500 rounded-l-[100px] rounded-r-4xl",
        "bg-light-neutral-900 px-3 py-3",
        "max-w-sm min-w-32",
        "flex flex-row items-center justify-between gap-x-4"
      )}
    >
      <Icon
        icon={props.icon}
        className={cn("w-6 h-6 flex-shrink-0", props.iconClassName)}
      />
      <Typography.Text fontSize="xs" className="text-white">
        {props.text}
      </Typography.Text>
      <button onClick={props.closeToast} className="cursor-pointer">
        <Icon icon="X" className={cn("w-6 h-6 flex-shrink-0 text-white")} />
      </button>
    </div>
  );
};

export const toasterMessages = {
  error: (text?: string) => {
    const styles = toastStyles["error"];
    toast((props) => (
      <BaseToast
        icon={styles.icon}
        iconClassName={cn(styles.iconColor)}
        text={text!}
        closeToast={props.closeToast}
      />
    ));
  },
  success: (text?: string) => {
    const styles = toastStyles["success"];
    toast((props) => (
      <BaseToast
        icon={styles.icon}
        iconClassName={cn(styles.iconColor)}
        text={text!}
        closeToast={props.closeToast}
      />
    ));
  },
  info: (text?: string) => {
    const styles = toastStyles["info"];
    toast((props) => (
      <BaseToast
        icon={styles.icon}
        iconClassName={cn(styles.iconColor)}
        text={text!}
        closeToast={props.closeToast}
      />
    ));
  },
  warning: (text?: string) => {
    const styles = toastStyles["warning"];
    toast((props) => (
      <BaseToast
        icon={styles.icon}
        iconClassName={cn(styles.iconColor)}
        text={text!}
        closeToast={props.closeToast}
      />
    ));
  },
};
