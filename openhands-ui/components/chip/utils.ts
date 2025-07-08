export type ChipVariant = "pill" | "corner";
export type ChipColor =
  | "primaryDark"
  | "primaryLight"
  | "green"
  | "red"
  | "aqua"
  | "gray";

export const chipStyles: Record<ChipColor, string> = {
  aqua: "border-aqua-500 text-aqua-500",
  gray: "border-light-neutral-400 text-light-neutral-400",
  green: "border-green-500 text-green-500",
  red: "border-red-400 text-red-400",
  primaryDark: "border-primary-400 text-primary-400",
  primaryLight: "border-primary-200 text-primary-200",
};
