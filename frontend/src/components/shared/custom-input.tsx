import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface CustomInputProps {
  testId?: string;
  name: string;
  label: string;
  required?: boolean;
  defaultValue?: string;
  type?: "text" | "password";
}

export function CustomInput({
  testId,
  name,
  label,
  required,
  defaultValue,
  type = "text",
}: CustomInputProps) {
  const { t } = useTranslation();

  return (
    <label data-testid={testId} htmlFor={name} className="flex flex-col gap-2">
      <span>unset</span>
      <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3]">
        {label}
        {required && <span className="text-[#FF4D4F]">*</span>}
        {!required && (
          <span className="text-[#A3A3A3]">
            {" "}
            {t(I18nKey.CUSTOM_INPUT$OPTIONAL_LABEL)}
          </span>
        )}
      </span>
      <input
        data-testid={`${testId}-input`}
        id={name}
        name={name}
        required={required}
        defaultValue={defaultValue}
        type={type}
        className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
      />
    </label>
  );
}
