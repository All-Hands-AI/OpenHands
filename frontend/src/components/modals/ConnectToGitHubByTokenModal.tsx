import { Form, useNavigation } from "@remix-run/react";
import { useTranslation } from "react-i18next";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalButton from "../buttons/ModalButton";
import AllHandsLogo from "#/assets/branding/all-hands-logo-spark.svg?react";
import ModalBody from "./ModalBody";
import { CustomInput } from "../form/custom-input";
import { I18nKey } from "#/i18n/declaration";

function ConnectToGitHubByTokenModal() {
  const navigation = useNavigation();
  const { t } = useTranslation();
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
            {t(
              I18nKey.CONNECT_TO_GITHUB_BY_TOKEN_MODAL$BY_CONNECTING_YOU_AGREE,
            )}{" "}
            <span className="text-hyperlink">
              {t(I18nKey.CONNECT_TO_GITHUB_BY_TOKEN_MODAL$TERMS_OF_SERVICE)}
            </span>
            .
          </p>
        </label>
        <ModalButton
          type="submit"
          text={t(I18nKey.CONNECT_TO_GITHUB_BY_TOKEN_MODAL$CONTINUE)}
          className="bg-[#791B80] w-full"
          disabled={navigation.state === "loading"}
        />
      </Form>
    </ModalBody>
  );
}

export default ConnectToGitHubByTokenModal;
