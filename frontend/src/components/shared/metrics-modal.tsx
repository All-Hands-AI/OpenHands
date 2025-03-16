import React from "react";
import { ModalBackdrop } from "./modals/modal-backdrop";
import { ModalBody } from "./modals/modal-body";
import { ModalButton } from "./buttons/modal-button";

interface MetricsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MetricsModal({ isOpen, onClose }: MetricsModalProps) {
  const [metrics, setMetrics] = React.useState<{
    cost: number | null;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    } | null;
  }>({
    cost: null,
    usage: null
  });

  React.useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data?.type === 'metrics_update') {
        setMetrics(event.data.metrics);
      }
    }

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  if (!isOpen) return null;

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody>
        <div className="flex flex-col gap-2 self-start w-full">
          <span className="text-xl leading-6 -tracking-[0.01em] font-semibold">
            Metrics Information
          </span>
          <div className="space-y-2">
            {metrics.cost !== null && (
              <p>Total Cost: ${metrics.cost.toFixed(4)}</p>
            )}
            {metrics.usage && (
              <>
                <p>Tokens Used:</p>
                <ul className="list-inside space-y-1 ml-2">
                  <li>- Input: {metrics.usage.prompt_tokens}</li>
                  <li>- Output: {metrics.usage.completion_tokens}</li>
                  <li>- Total: {metrics.usage.total_tokens}</li>
                </ul>
              </>
            )}
            {!metrics.cost && !metrics.usage && (
              <p className="text-neutral-400">No metrics data available</p>
            )}
          </div>
        </div>
        <div className="flex justify-end w-full">
          <ModalButton
            onClick={onClose}
            text="Close"
            className="bg-neutral-700 hover:bg-neutral-600"
          />
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
