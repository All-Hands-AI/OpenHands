import { useMemo } from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import "./index.css";

type BaseSpinnerProps = HTMLProps<"svg">;

export type DeterminateSpinnerProps = BaseSpinnerProps & {
  determinate: true;
  value: number;
  variant?: never;
};

export type IndeterminateSpinnerProps = BaseSpinnerProps & {
  determinate?: false | null | undefined;
  value?: never;
  variant?: "simple" | "dynamic";
};

export type SpinnerProps = DeterminateSpinnerProps | IndeterminateSpinnerProps;

const SIZE = 48;
const STROKE_WIDTH = 6;
const radius = (SIZE - STROKE_WIDTH) / 2;
const circumference = 2 * Math.PI * radius;

export const Spinner = ({
  value = 10,
  determinate = false,
  variant = "simple",
  className,
  ...props
}: SpinnerProps) => {
  const offset = useMemo(
    () => circumference - (value / 100) * circumference,
    [value]
  );

  return (
    <svg width={SIZE} height={SIZE} className={className} {...props}>
      <circle
        cx={SIZE / 2}
        cy={SIZE / 2}
        r={radius}
        fill="none"
        className="stroke-grey-970"
        strokeWidth={STROKE_WIDTH}
      />
      {determinate ? (
        <g>
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={radius}
            fill="none"
            className="stroke-primary-500 animate-determinate-spinner"
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          />
        </g>
      ) : variant === "simple" ? (
        <g className="animate-indeterminate-spinner origin-center">
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={radius}
            fill="none"
            className="stroke-primary-500"
            strokeWidth={STROKE_WIDTH}
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.75}
            strokeLinecap="round"
            transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          />
        </g>
      ) : (
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={radius}
          fill="none"
          className="stroke-primary-500 animate-dynamic-spinner origin-center"
          strokeWidth={STROKE_WIDTH}
          strokeDasharray={circumference}
          strokeDashoffset={circumference * 0.75}
          strokeLinecap="round"
        />
      )}
    </svg>
  );
};
