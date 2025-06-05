import { Spinner } from "@heroui/react";
import { ModalBody } from "#/components/shared/modals/modal-body";

export function LoadingMicroagentBody() {
  return (
    <ModalBody>
      <h2 className="font-bold text-[20px] leading-6 -tracking-[0.01em] flex items-center gap-2">
        Add to Microagent
      </h2>
      <Spinner size="lg" />
      <p>Please wait for the runtime to be active.</p>
    </ModalBody>
  );
}
