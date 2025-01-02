interface PathFormProps {
  ref: React.RefObject<HTMLFormElement | null>;
  onBlur: () => void;
}

export function PathForm({ ref, onBlur }: PathFormProps) {
  return (
    <form ref={ref} className="flex-1">
      <input
        name="path"
        type="text"
        className="w-full bg-transparent"
        onBlur={onBlur}
      />
    </form>
  );
}
