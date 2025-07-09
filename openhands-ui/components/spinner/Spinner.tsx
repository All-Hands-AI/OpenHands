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
      {/* Background circle */}
      <circle
        cx={SIZE / 2}
        cy={SIZE / 2}
        r={radius}
        fill="none"
        className="stroke-grey-970"
        strokeWidth={STROKE_WIDTH}
      />
      
      {determinate ? (
        // Determinate spinner
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={radius}
          fill="none"
          className="stroke-primary-500"
          strokeWidth={STROKE_WIDTH}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          style={{
            transition: "stroke-dashoffset 0.3s ease"
          }}
        />
      ) : variant === "simple" ? (
        // Simple indeterminate spinner
        <g 
          style={{
            transformOrigin: "center",
            animation: "2s linear infinite spinner-simple-rotate"
          }}
        >
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
        // Dynamic indeterminate spinner
        <g 
          style={{
            transformOrigin: "center",
            animation: "1.8s cubic-bezier(0.65, 0, 0.35, 1) infinite spinner-dynamic-rotate"
          }}
        >
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
            style={{
              animation: "1.8s cubic-bezier(0.65, 0, 0.35, 1) infinite spinner-dynamic-arc"
            }}
          />
        </g>
      )}
    </svg>
  );
};
