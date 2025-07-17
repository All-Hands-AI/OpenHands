import { Spinner } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { ModalBody } from "#/components/shared/modals/modal-body";

export function LoadingMicroagentBody() {
  const { t } = useTranslation();
  return (
    <ModalBody>
      <h2 className="font-bold text-[20px] leading-6 -tracking-[0.01em] flex items-center gap-2">
        {t("MICROAGENT$ADD_TO_MICROAGENT")}
      </h2>
      <Spinner size="lg" />
      <p>{t("MICROAGENT$WAIT_FOR_RUNTIME")}</p>
    </ModalBody>
  );
}
