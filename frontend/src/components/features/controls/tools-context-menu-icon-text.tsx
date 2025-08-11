interface ToolsContextMenuIconTextProps {
  icon: React.ReactNode;
  text: string;
  rightIcon?: React.ReactNode;
}

export function ToolsContextMenuIconText({
  icon,
  text,
  rightIcon,
}: ToolsContextMenuIconTextProps) {
  return (
    <div className="flex items-center justify-between p-2 hover:bg-[#5C5D62] rounded">
      <div className="flex items-center gap-2">
        {icon}
        {text}
      </div>
      {rightIcon && <div className="flex items-center">{rightIcon}</div>}
    </div>
  );
}
