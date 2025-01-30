interface SettingsInputProps {
  testId?: string;
  label: string;
  type: React.HTMLInputTypeAttribute;
}

export function SettingsInput({ testId, label, type }: SettingsInputProps) {
  return (
    <label className="flex flex-col gap-2.5">
      <span className="text-sm">{label}</span>
      <input
        data-testid={testId}
        type={type}
        className="bg-[#454545] border border-[#717888] h-10 w-[680px] rounded p-2"
      />
    </label>
  );
}
