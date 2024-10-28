interface ErrorMessageProps {
  error: string;
  message: string;
}

export function ErrorMessage({ error, message }: ErrorMessageProps) {
  return (
    <div className="flex gap-2 items-center justify-start border-l-2 border-danger pl-2 my-2 py-2">
      <div className="text-sm leading-4 flex flex-col gap-2">
        <p className="text-danger font-bold">{error}</p>
        <p className="text-neutral-300">{message}</p>
      </div>
    </div>
  );
}
