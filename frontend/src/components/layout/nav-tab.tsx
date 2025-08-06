import { ComponentType } from "react";
import { Tooltip } from "@heroui/react";
import { NavLink } from "react-router";
import { cn } from "#/utils/utils";
// import { LoadingSpinner } from "../shared/loading-spinner";

interface NavTabProps {
  to: string;
  icon: ComponentType<{ className: string }>;
  rightContent?: React.ReactNode;
}

export function NavTab({ to, icon: Icon, rightContent }: NavTabProps) {
  const showTooltip = !!rightContent;
  const content = (isActive: boolean) => (
    <div
      className={cn(
        "p-1 rounded-md",
        "text-[#9299AA] bg-[#0D0F11]",
        isActive && "bg-[#25272D]",
        isActive
          ? "hover:text-white hover:bg-tertiary"
          : "hover:text-white hover:bg-[#0D0F11]",
        isActive
          ? "focus-within:text-white focus-within:bg-tertiary"
          : "focus-within:text-white focus-within:bg-[#0D0F11]",
      )}
    >
      <Icon className={cn("w-5 h-5 text-inherit")} />

      {/* {isLoading && <LoadingSpinner size="small" />} */}
    </div>
  );
  return (
    <NavLink end key={to} to={to} tabIndex={0} className="group">
      {({ isActive }) => {
        if (showTooltip) {
          return (
            <Tooltip
              showArrow
              content={<div>{rightContent}</div>}
              closeDelay={100}
              placement="right"
              classNames={{
                base: "before:bg-tertiary before:w-4 before:h-4",

                content:
                  "p-1 rounded-sm text-[#9299AA] bg-tertiary cursor-pointer hover:text-white",
              }}
            >
              {content(isActive)}
            </Tooltip>
          );
        }
        return content(isActive);
      }}
    </NavLink>
  );
}
