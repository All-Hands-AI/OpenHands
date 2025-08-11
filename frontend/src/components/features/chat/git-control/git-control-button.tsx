import { ReactNode, ButtonHTMLAttributes, AnchorHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import LinkExternalIcon from "#/icons/link-external.svg?react";
import { cn } from "#/utils/utils";

const gitControlButtonVariants = cva(
  "group flex flex-row items-center rounded-[100px]",
  {
    variants: {
      size: {
        compact: "px-0.5 py-1 justify-center gap-1",
        wide: "pl-2.5 pr-2.5 py-1 justify-between",
        "extra-wide": "px-2 py-1 h-7 justify-center gap-[11px]",
      },
      width: {
        small: "w-[76px]",
        medium: "w-[77px]",
        large: "w-[126px]",
        "extra-large": "w-52",
      },
      enabled: {
        true: "bg-[#25272D] hover:bg-[#525662] cursor-pointer",
        false: "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      },
    },
    defaultVariants: {
      size: "compact",
      width: "small",
      enabled: true,
    },
  },
);

type BaseProps = {
  icon: ReactNode;
  text: ReactNode;
  showExternalLink?: boolean;
} & VariantProps<typeof gitControlButtonVariants>;

type ButtonProps = BaseProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
    as?: "button";
  };

type AnchorProps = BaseProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "children"> & {
    as: "a";
  };

export type GitControlButtonProps = ButtonProps | AnchorProps;

export function GitControlButton({
  size,
  width,
  enabled = true,
  icon,
  text,
  showExternalLink = false,
  className,
  ...restProps
}: GitControlButtonProps) {
  const content = (
    <>
      <div className="flex flex-row gap-2 items-center justify-start">
        <div className="w-3 h-3 flex items-center justify-center">{icon}</div>
        <div className="font-normal text-white text-sm leading-5">{text}</div>
      </div>
      {showExternalLink && enabled && (
        <div className="w-3 h-3 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <LinkExternalIcon width={12} height={12} color="white" />
        </div>
      )}
    </>
  );

  if ((restProps as AnchorProps).as === "a") {
    const anchorProps = restProps as Omit<AnchorProps, keyof BaseProps>;
    return (
      <a
        className={cn(
          gitControlButtonVariants({ size, width, enabled }),
          className,
        )}
        href={anchorProps.href}
        target={anchorProps.target}
        rel={anchorProps.rel}
        onClick={anchorProps.onClick}
      >
        {content}
      </a>
    );
  }

  const buttonProps = restProps as Omit<ButtonProps, keyof BaseProps>;
  return (
    <button
      type="button"
      disabled={!enabled}
      className={cn(
        gitControlButtonVariants({ size, width, enabled }),
        className,
      )}
      onClick={buttonProps.onClick}
    >
      {content}
    </button>
  );
}
