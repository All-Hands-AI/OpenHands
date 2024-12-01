import { Card } from "@nextui-org/react";

interface ErrorMessageProps {
  message: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <Card
      data-testid="error-message"
      className="bg-danger-50 text-danger-foreground p-4 mb-4"
    >
      {message}
    </Card>
  );
}
