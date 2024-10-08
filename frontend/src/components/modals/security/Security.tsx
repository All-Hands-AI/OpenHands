import React from "react";
import SecurityInvariant from "./invariant/Invariant";
import BaseModal from "../base-modal/BaseModal";

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
  const AnalyzerComponent =
    securityAnalyzer &&
    SecurityAnalyzers[securityAnalyzer as SecurityAnalyzerOption]
      ? SecurityAnalyzers[securityAnalyzer as SecurityAnalyzerOption]
      : () => <div>Unknown security analyzer chosen</div>;

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
