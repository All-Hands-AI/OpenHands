import { Form, useNavigation } from "@remix-run/react";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalButton from "../buttons/ModalButton";
import AllHandsLogo from "#/assets/branding/all-hands-logo-spark.svg?react";
import ModalBody from "./ModalBody";

interface CustomInputProps {
  name: string;
  label: string;
  required?: boolean;
}

function CustomInput({ name, label, required }: CustomInputProps) {
  return (
    <label htmlFor={name} className="flex flex-col gap-2">
      <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3]">
        {label}
        {required && <span className="text-[#FF4D4F]">*</span>}
        {!required && <span className="text-[#A3A3A3]"> (optional)</span>}
      </span>
      <input
        id={name}
        name={name}
        type="text"
        className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
      />
    </label>
  );
}

function ConnectToGitHubByTokenModal() {
  const navigation = useNavigation();

  return (
    <ModalBody testID="auth-modal">
      <div className="flex flex-col gap-2">
        <AllHandsLogo width={69} height={46} className="self-center" />
        <BaseModalTitle title="Ready to experience the future?" />
        <BaseModalDescription description="Connect All Hands to your GitHub account to start building." />
      </div>
      <Form className="w-full flex flex-col gap-6" method="post" action="/">
        <CustomInput label="GitHub Token" name="token" />
        <label htmlFor="tos" className="flex gap-2">
          <input
            data-testid="accept-terms"
            id="tos"
            name="tos"
            type="checkbox"
            required
          />
          <p className="text-xs text-[#A3A3A3]">
            By connecting you agree to our{" "}
            <span className="text-hyperlink">terms of service</span>.
          </p>
        </label>
        <ModalButton
          type="submit"
          text="Continue"
          className="bg-[#791B80] w-full"
          loading={navigation.state === "loading"}
        />
      </Form>
    </ModalBody>
  );
}

export default ConnectToGitHubByTokenModal;
