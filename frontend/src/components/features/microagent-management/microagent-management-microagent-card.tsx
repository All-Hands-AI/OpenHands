import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export interface Microagent {
  id: string;
  name: string;
  repositoryUrl: string;
  createdAt: string;
}

interface MicroagentManagementMicroagentCardProps {
  microagent: Microagent;
}

export function MicroagentManagementMicroagentCard({
  microagent,
}: MicroagentManagementMicroagentCardProps) {
  const { t } = useTranslation();

  return (
    <div className="rounded-lg bg-[#ffffff0d] border border-[#ffffff33] p-4 cursor-pointer hover:bg-[#ffffff33] hover:border-[#C9B974] transition-all duration-300">
      <div className="text-white text-[16px] font-semibold">
        {microagent.name}
      </div>
      <div className="text-white text-sm font-normal">
        {microagent.repositoryUrl}
      </div>
      <div className="text-white text-sm font-normal">
        {t(I18nKey.COMMON$CREATED_ON)} {microagent.createdAt}
      </div>
    </div>
  );
}
