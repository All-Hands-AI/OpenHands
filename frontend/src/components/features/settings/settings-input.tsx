import { cn } from "#/utils/utils";
import { OptionalTag } from "./optional-tag";

interface SettingsInputProps {
  testId?: string;
  name?: string;
  label: string;
  type: React.HTMLInputTypeAttribute;
  defaultValue?: string;
  placeholder?: string;
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  badgeContent?: string;
  className?: string;
}

export function SettingsInput({
  testId,
  name,
  label,
  type,
  defaultValue,
  placeholder,
  showOptionalTag,
  isDisabled,
  badgeContent,
  className,
}: SettingsInputProps) {
  return (
    <label className={cn("flex flex-col gap-2.5 w-fit", className)}>
      <div className="flex items-center gap-1">
        <span className="text-sm">{label}</span>
        {badgeContent && (
          <span
            data-testid="badge"
            className="border border-[#C9B974] text-[#C9B974] rounded text-xs font-bold px-1"
          >
            {badgeContent}
          </span>
        )}
        {showOptionalTag && <OptionalTag />}
      </div>
      <input
        data-testid={testId}
        name={name}
        disabled={isDisabled}
        type={type}
        defaultValue={defaultValue}
        placeholder={placeholder}
        className={cn(
          "bg-[#454545] border border-[#717888] h-10 w-full rounded p-2 placeholder:italic",
          "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
        )}
      />
    </label>
  );
}
