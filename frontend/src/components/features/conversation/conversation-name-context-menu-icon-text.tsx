interface ConversationNameContextMenuIconTextProps {
  icon: React.ReactNode;
  text: string;
}

export function ConversationNameContextMenuIconText({
  icon,
  text,
}: ConversationNameContextMenuIconTextProps) {
  return (
    <div className="flex items-center gap-2 p-2 hover:bg-[#5C5D62] rounded">
      {icon}
      {text}
    </div>
  );
}
