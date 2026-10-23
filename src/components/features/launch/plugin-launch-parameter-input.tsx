import { SettingsInput } from "#/components/features/settings/settings-input";

export interface PluginLaunchParameterInputProps {
  pluginIndex: number;
  paramKey: string;
  paramValue: unknown;
  /** Manifest schema options: renders a select instead of free text. */
  options?: string[];
  /** Manifest schema description, shown as helper text. */
  helpText?: string;
  onParameterChange: (
    pluginIndex: number,
    paramKey: string,
    value: unknown,
  ) => void;
}

export function PluginLaunchParameterInput({
  pluginIndex,
  paramKey,
  paramValue,
  options,
  helpText,
  onParameterChange,
}: PluginLaunchParameterInputProps) {
  const inputId = `plugin-${pluginIndex}-param-${paramKey}`;

  if (options && options.length > 0) {
    return (
      <label htmlFor={inputId} className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-contrast">{paramKey}</span>
        <select
          id={inputId}
          data-testid={inputId}
          value={String(paramValue ?? "")}
          onChange={(e) =>
            onParameterChange(pluginIndex, paramKey, e.target.value)
          }
          className="w-full rounded-md border border-border bg-basic px-3 py-2"
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        {helpText && <span className="text-xs text-contrast">{helpText}</span>}
      </label>
    );
  }

  if (typeof paramValue === "boolean") {
    return (
      <label
        htmlFor={inputId}
        className="flex w-full cursor-pointer items-center gap-2.5"
      >
        <input
          id={inputId}
          data-testid={inputId}
          type="checkbox"
          checked={paramValue}
          onChange={(e) =>
            onParameterChange(pluginIndex, paramKey, e.target.checked)
          }
          className="h-4 w-4 shrink-0 rounded"
        />
        <span className="text-sm">{paramKey}</span>
      </label>
    );
  }

  if (typeof paramValue === "number") {
    return (
      <SettingsInput
        testId={inputId}
        name={`plugin-${pluginIndex}-param-${paramKey}`}
        type="number"
        label={paramKey}
        value={String(paramValue)}
        className="w-full"
        onChange={(value) =>
          onParameterChange(
            pluginIndex,
            paramKey,
            value === "" ? 0 : parseFloat(value) || 0,
          )
        }
      />
    );
  }

  return (
    <SettingsInput
      testId={inputId}
      name={`plugin-${pluginIndex}-param-${paramKey}`}
      type="text"
      label={paramKey}
      value={String(paramValue ?? "")}
      className="w-full"
      onChange={(value) => onParameterChange(pluginIndex, paramKey, value)}
      {...(helpText ? { helpText } : {})}
    />
  );
}
