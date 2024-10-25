import { FeedbackForm } from "#/components/feedback-form";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/modals/confirmation-modals/BaseModal";
import ModalBody from "#/components/modals/ModalBody";

function TestBed() {
  return (
    <div className="flex items-center justify-center h-screen">
      <ModalBody className="text-start">
        <BaseModalTitle title="Feedback" />
        <BaseModalDescription description="To help us improve, we collect feedback from your interactions to improve our prompts. By submitting this form, you consent to us collecting this data." />
        <FeedbackForm />
      </ModalBody>
    </div>
  );
}

export default TestBed;
