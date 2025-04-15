interface PathFormProps {
  ref: React.RefObject<HTMLFormElement | null>;
  onBlur: () => void;
  defaultValue: string;
}

export function PathForm({ ref, onBlur, defaultValue }: PathFormProps) {
  return (
    <form ref={ref} onSubmit={(e) => e.preventDefault()} className="flex-1">
      <input
        name="url"
        type="text"
        defaultValue={defaultValue}
        className="w-full bg-transparent"
        onBlur={onBlur}
      />
    </form>
  );
}
