import { cn } from "#/utils/utils";

interface SettingsInputProps {
  testId?: string;
  label: string;
  type: React.HTMLInputTypeAttribute;
  className?: string;
}

export function SettingsInput({
  testId,
  label,
  type,
  className,
}: SettingsInputProps) {
  return (
    <label className={cn("flex flex-col gap-2.5 w-fit", className)}>
      <span className="text-sm">{label}</span>
      <input
        data-testid={testId}
        type={type}
        className="bg-[#454545] border border-[#717888] h-10 w-full rounded p-2"
      />
    </label>
  );
}
