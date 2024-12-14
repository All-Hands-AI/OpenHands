import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BaseModal } from "../base-modal";
import { BaseModalTitle } from "../base-modal-title";
import { BaseModalDescription } from "../base-modal-description";
import { Button } from "../../buttons/button";

interface CreateInstructionsModalProps {
  repoName: string;
  onClose: () => void;
  onCreateInstructions: (instructions: string) => void;
}

export function CreateInstructionsModal({
  repoName,
  onClose,
  onCreateInstructions,
}: CreateInstructionsModalProps) {
  const { t } = useTranslation();

  const [instructions, setInstructions] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreateInstructions(instructions);
    onClose();
  };

  return (
    <BaseModal onClose={onClose}>
      <form
        onSubmit={handleSubmit}
        className="bg-root-primary w-[384px] p-6 rounded-xl flex flex-col gap-4"
      >
        <BaseModalTitle title={t(I18nKey.CREATE_INSTRUCTIONS_MODAL$TITLE)} />
        <BaseModalDescription>
          {t(I18nKey.CREATE_INSTRUCTIONS_MODAL$DESCRIPTION, { repoName })}
        </BaseModalDescription>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Enter repository instructions"
          className="w-full h-48 p-2 mt-4 mb-4 bg-[#262626] text-white rounded-lg resize-none"
        />
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            text={t(I18nKey.CREATE_INSTRUCTIONS_MODAL$CANCEL_BUTTON)}
          />
          <Button
            type="submit"
            variant="primary"
            text={t(I18nKey.CREATE_INSTRUCTIONS_MODAL$CREATE_BUTTON)}
          />
        </div>
      </form>
    </BaseModal>
  );
}
