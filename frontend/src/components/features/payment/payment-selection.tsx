interface PaymentSelectionProps {
  options: number[];
  onPaymentSelection: (amount: number) => void;
}

export function PaymentSelection({
  options,
  onPaymentSelection,
}: PaymentSelectionProps) {
  return (
    <div className="flex flex-col gap-1">
      <p>Please select your desired amount:</p>
      <div className="flex gap-2">
        {options.map((option) => (
          <button
            type="button"
            key={option}
            data-testid={`option-${option}`}
            onClick={() => onPaymentSelection(option)}
            className="text-xs font-semibold border rounded-md px-2 py-0.5"
          >
            ${option}
          </button>
        ))}
      </div>
    </div>
  );
}
