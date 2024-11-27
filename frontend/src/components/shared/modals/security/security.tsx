import React from "react";
import { useTranslation } from "react-i18next";
import SecurityInvariant from "./invariant/invariant";
import { I18nKey } from "#/i18n/declaration";
import { BaseModal } from "../base-modal/base-modal";

interface SecurityProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  securityAnalyzer: string;
}

enum SecurityAnalyzerOption {
  INVARIANT = "invariant",
}

const SecurityAnalyzers: Record<SecurityAnalyzerOption, React.ElementType> = {
  [SecurityAnalyzerOption.INVARIANT]: SecurityInvariant,
};

function Security({ isOpen, onOpenChange, securityAnalyzer }: SecurityProps) {
  const { t } = useTranslation();

  const AnalyzerComponent =
    securityAnalyzer &&
    SecurityAnalyzers[securityAnalyzer as SecurityAnalyzerOption]
      ? SecurityAnalyzers[securityAnalyzer as SecurityAnalyzerOption]
      : () => <div>{t(I18nKey.SECURITY$UNKNOWN_ANALYZER_LABEL)}</div>;

  return (
    <BaseModal
      isOpen={isOpen && !!securityAnalyzer}
      contentClassName="max-w-[80%] h-[80%]"
      bodyClassName="px-0 py-0 max-h-[100%]"
      onOpenChange={onOpenChange}
      title=""
    >
      <AnalyzerComponent />
    </BaseModal>
  );
}

export default Security;
