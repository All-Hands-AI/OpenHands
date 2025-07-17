import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface MicroagentManagementLearnThisRepoProps {
  repositoryUrl: string;
}

export function MicroagentManagementLearnThisRepo({
  repositoryUrl,
}: MicroagentManagementLearnThisRepoProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-center rounded-lg bg-[#ffffff0d] border border-dashed border-[#ffffff4d] p-4 hover:bg-[#ffffff33] hover:border-[#C9B974] transition-all duration-300 cursor-pointer">
      <a
        className="text-[16px] font-normal text-[#8480FF]"
        href={repositoryUrl}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t(I18nKey.MICROAGENT_MANAGEMENT$LEARN_THIS_REPO)}
      </a>
    </div>
  );
}
