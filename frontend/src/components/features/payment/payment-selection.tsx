import React from "react";

interface PaymentSelectionProps {
  options: number[];
  onPaymentSelection: (amount: number) => void;
}

export function PaymentSelection({
  options,
  onPaymentSelection,
}: PaymentSelectionProps) {
  const [selectedOption, setSelectedOption] = React.useState<number | null>(
    null,
  );

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (selectedOption) onPaymentSelection(selectedOption);
  };

  return (
    <form onSubmit={handleSubmit}>
      {options.map((option) => (
        <button
          type="button"
          key={option}
          data-testid={`option-${option}`}
          onClick={() => setSelectedOption(option)}
        >
          {option}
        </button>
      ))}

      <button type="submit" disabled={!selectedOption}>
        Confirm
      </button>
    </form>
  );
}
