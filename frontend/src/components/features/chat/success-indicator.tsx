import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";

interface SuccessIndicatorProps {
  success: boolean;
}

export function SuccessIndicator({ success }: SuccessIndicatorProps) {
  return (
    <span className="flex-shrink-0">
      {success && (
        <CheckCircle
          data-testid="status-icon"
          className="h-4 w-4 ml-2 inline fill-success"
        />
      )}

      {!success && (
        <XCircle
          data-testid="status-icon"
          className="h-4 w-4 ml-2 inline fill-danger"
        />
      )}
    </span>
  );
}
