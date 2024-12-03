interface ProjectStateIndicatorProps {
  state: "cold" | "warm";
}

export function ProjectStateIndicator({ state }: ProjectStateIndicatorProps) {
  return (
    <div
      data-testid={`${state}-indicator`}
      className="w-[18px] h-[18px] rounded-full border border-yellow-500"
    />
  );
}
