interface TOSCheckboxProps {
  onChange: () => void;
}

export function TOSCheckbox({ onChange }: TOSCheckboxProps) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" onChange={onChange} />
      <span>
        I accept the{" "}
        <a
          href="https://www.all-hands.dev/tos"
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 text-blue-500 hover:text-blue-700"
        >
          terms of service
        </a>
      </span>
    </label>
  );
}
