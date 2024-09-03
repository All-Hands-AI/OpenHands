import React from "react";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalButton from "../buttons/ModalButton";
import AllHandsLogo from "#/assets/branding/all-hands-logo-spark.svg?react";
import GitHubLogo from "#/assets/branding/github-logo.svg?react";
import ModalBody from "./ModalBody";

function ConnectToGitHubModal() {
  return (
    <ModalBody>
      <div className="flex flex-col gap-2">
        <AllHandsLogo width={69} height={46} className="self-center" />
        <BaseModalTitle title="Ready to experience the future?" />
        <BaseModalDescription description="Connect All Hands to your GitHub account to start building." />
      </div>
      <ModalButton
        text="Connect to GitHub"
        className="bg-[#791B80] w-full"
        onClick={() => console.log("Connect to GitHub")}
        icon={<GitHubLogo width={20} height={20} />}
      />
      <p className="text-xs text-[#A3A3A3]">
        By connecting you agree to our{" "}
        <span className="text-hyperlink">terms of service</span>.
      </p>
    </ModalBody>
  );
}

export default ConnectToGitHubModal;
