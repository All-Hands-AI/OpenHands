import { ReactNode } from "react";

interface MetricRowProps {
  label: ReactNode;
  value: ReactNode;
  labelClassName?: string;
  valueClassName?: string;
}

export function MetricRow({
  label,
  value,
  labelClassName = "",
  valueClassName = "font-semibold",
}: MetricRowProps) {
  return (
    <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
      <span className={labelClassName}>{label}</span>
      <span className={valueClassName}>{value}</span>
    </div>
  );
}
