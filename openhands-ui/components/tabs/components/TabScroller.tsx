import { cn } from "../../../shared/utils/cn";
import { Icon, type IconProps } from "../../icon/Icon";

type TabScrollerProps = {
  position: "left" | "right";
  onScroll(): void;
};

const tabScrollMetadata: Record<
  TabScrollerProps["position"],
  { className: string; icon: IconProps["icon"] }
> = {
  left: {
    className: cn("rounded-tl-2xl"),
    icon: "ChevronDoubleLeft",
  },
  right: {
    className: cn("rounded-tr-2xl"),
    icon: "ChevronDoubleRight",
  },
};

export const TabScroller = ({ position, onScroll }: TabScrollerProps) => {
  const { className, icon } = tabScrollMetadata[position];

  return (
    <button
      onClick={onScroll}
      className={cn(
        "border-1 border-light-neutral-500",
        "flex flex-row items-center px-4",
        "bg-light-neutral-970",
        "enabled:hover:bg-light-neutral-500",
        "enabled:focus:bg-light-neutral-970",
        "enabled:active:bg-grey-970",
        className
      )}
      aria-label={`Scroll tabs ${position}`}
    >
      <Icon icon={icon} className={cn("w-4.5 h-4.5 text-primary-500")} />
    </button>
  );
};
