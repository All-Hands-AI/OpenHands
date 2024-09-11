interface CustomInputProps {
  name: string;
  label: string;
  required?: boolean;
}

export function CustomInput({ name, label, required }: CustomInputProps) {
  return (
    <label htmlFor={name} className="flex flex-col gap-2">
      <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3]">
        {label}
        {required && <span className="text-[#FF4D4F]">*</span>}
        {!required && <span className="text-[#A3A3A3]"> (optional)</span>}
      </span>
      <input
        id={name}
        name={name}
        required={required}
        type="text"
        className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
      />
    </label>
  );
}
