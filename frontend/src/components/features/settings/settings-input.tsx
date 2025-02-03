import { cn } from "#/utils/utils";
import { OptionalTag } from "./optional-tag";

interface SettingsInputProps {
  testId?: string;
  label: string;
  type: React.HTMLInputTypeAttribute;
  placeholder?: string;
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  className?: string;
}

export function SettingsInput({
  testId,
  label,
  type,
  placeholder,
  showOptionalTag,
  isDisabled,
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
        disabled={isDisabled}
        type={type}
        placeholder={placeholder}
        className={cn(
          "bg-[#454545] border border-[#717888] h-10 w-full rounded p-2 placeholder:italic",
          "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
        )}
      />
    </label>
  );
}
