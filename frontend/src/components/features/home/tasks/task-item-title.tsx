import { Typography } from "@openhands/ui";

export function TaskItemTitle({ children: title }: React.PropsWithChildren) {
  return (
    <div className="py-3">
      <Typography.H3 className="text-sm text-white leading-6 font-medium">
        {title}
      </Typography.H3>
    </div>
  );
}
