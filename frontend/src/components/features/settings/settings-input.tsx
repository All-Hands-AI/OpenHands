import { cn } from "#/utils/utils";
import { OptionalTag } from "./optional-tag";

interface SettingsInputProps {
  testId?: string;
  label: string;
  type: React.HTMLInputTypeAttribute;
  showOptionalTag?: boolean;
  className?: string;
}

export function SettingsInput({
  testId,
  label,
  type,
  showOptionalTag,
  className,
}: SettingsInputProps) {
  return (
    <label className={cn("flex flex-col gap-2.5 w-fit", className)}>
      <div className="flex items-center gap-1">
        <span className="text-sm">{label}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
      <input
        data-testid={testId}
        type={type}
        className="bg-[#454545] border border-[#717888] h-10 w-full rounded p-2"
      />
    </label>
  );
}
