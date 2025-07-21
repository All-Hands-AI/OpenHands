import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { formatDateMMDDYYYY } from "#/utils/format-time-delta";

interface MicroagentManagementMicroagentCardProps {
  microagent: {
    id: string;
    name: string;
    createdAt: string;
  };
}

export function MicroagentManagementMicroagentCard({
  microagent,
}: MicroagentManagementMicroagentCardProps) {
  const { t } = useTranslation();

  // Format the repository URL to point to the microagent file
  const microagentFilePath = `.openhands/microagents/${microagent.name}`;

  // Format the createdAt date using MM/DD/YYYY format
  const formattedCreatedAt = formatDateMMDDYYYY(new Date(microagent.createdAt));

  return (
    <div className="rounded-lg bg-[#ffffff0d] border border-[#ffffff33] p-4 cursor-pointer hover:bg-[#ffffff33] hover:border-[#C9B974] transition-all duration-300">
      <div className="text-white text-[16px] font-semibold">
        {microagent.name}
      </div>
      <div className="text-white text-sm font-normal">{microagentFilePath}</div>
      <div className="text-white text-sm font-normal">
        {t(I18nKey.COMMON$CREATED_ON)} {formattedCreatedAt}
      </div>
    </div>
  );
}
