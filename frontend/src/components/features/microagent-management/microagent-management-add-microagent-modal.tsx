import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { FaCircleInfo } from "react-icons/fa6";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import XIcon from "#/icons/x.svg?react";
import { cn } from "#/utils/utils";
import { BadgeInput } from "#/components/shared/inputs/badge-input";

interface MicroagentManagementAddMicroagentModalProps {
  onConfirm: () => void;
  onCancel: () => void;
}

export function MicroagentManagementAddMicroagentModal({
  onConfirm,
  onCancel,
}: MicroagentManagementAddMicroagentModalProps) {
  const { t } = useTranslation();

  const [triggers, setTriggers] = useState<string[]>([]);

  const { selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const modalTitle = selectedRepository
    ? `${t(I18nKey.MICROAGENT_MANAGEMENT$ADD_A_MICROAGENT_TO)} ${selectedRepository}`
    : t(I18nKey.MICROAGENT_MANAGEMENT$ADD_A_MICROAGENT);

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
  };

  return (
    <ModalBackdrop>
      <ModalBody className="items-start rounded-[12px] p-6 min-w-[611px]">
        <div className="flex flex-col gap-2 w-full">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <h2 className="text-white text-xl font-medium">{modalTitle}</h2>
              <a
                href="https://docs.all-hands.dev/usage/prompting/microagents-overview#microagents-overview"
                target="_blank"
                rel="noopener noreferrer"
              >
                <FaCircleInfo className="text-primary" />
              </a>
            </div>
            <button type="button" onClick={onCancel} className="cursor-pointer">
              <XIcon width={24} height={24} color="#F9FBFE" />
            </button>
          </div>
          <span className="text-white text-sm font-normal">
            {t(I18nKey.MICROAGENT_MANAGEMENT$ADD_MICROAGENT_MODAL_DESCRIPTION)}
          </span>
        </div>
        <form
          data-testid="add-microagent-modal"
          onSubmit={onSubmit}
          className="flex flex-col gap-6 w-full"
        >
          <label
            htmlFor="query-input"
            className="flex flex-col gap-2 w-full text-sm font-normal"
          >
            {t(I18nKey.MICROAGENT_MANAGEMENT$WHAT_TO_DO)}
            <textarea
              required
              data-testid="query-input"
              name="query-input"
              placeholder={t(I18nKey.MICROAGENT_MANAGEMENT$DESCRIBE_WHAT_TO_DO)}
              rows={6}
              className={cn(
                "bg-tertiary border border-[#717888] bg-[#454545] w-full rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt resize-none",
                "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
              )}
            />
            <div className="flex items-center gap-2 text-[11px] font-normal text-white leading-[16px]">
              <span className="font-semibold">
                {t(I18nKey.COMMON$FOR_EXAMPLE)}:
              </span>
              <span className="underline">
                {t(I18nKey.COMMON$TEST_DB_MIGRATION)}
              </span>
              <span className="underline">{t(I18nKey.COMMON$RUN_TEST)}</span>
              <span className="underline">{t(I18nKey.COMMON$RUN_APP)}</span>
              <span className="underline">
                {t(I18nKey.COMMON$LEARN_FILE_STRUCTURE)}
              </span>
            </div>
          </label>
          <label
            htmlFor="trigger-input"
            className="flex flex-col gap-2.5 w-full text-sm"
          >
            <div className="flex items-center gap-2">
              {t(I18nKey.MICROAGENT_MANAGEMENT$ADD_TRIGGERS)}
              <a
                href="https://docs.all-hands.dev/usage/prompting/microagents-keyword"
                target="_blank"
                rel="noopener noreferrer"
              >
                <FaCircleInfo className="text-primary" />
              </a>
            </div>
            <BadgeInput
              name="trigger-input"
              value={triggers}
              placeholder={t("MICROAGENT$TYPE_TRIGGER_SPACE")}
              onChange={setTriggers}
            />
            <span className="text-xs text-[#ffffff80] font-normal">
              {t(
                I18nKey.MICROAGENT_MANAGEMENT$HELP_TEXT_DESCRIBING_VALID_TRIGGERS,
              )}
            </span>
          </label>
        </form>
        <div
          className="flex items-center justify-end gap-2 w-full"
          onClick={(event) => event.stopPropagation()}
        >
          <BrandButton
            type="button"
            variant="secondary"
            onClick={onCancel}
            data-testid="cancel-button"
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
          <BrandButton
            type="button"
            variant="primary"
            onClick={onConfirm}
            data-testid="confirm-button"
          >
            {t(I18nKey.MICROAGENT$LAUNCH)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
