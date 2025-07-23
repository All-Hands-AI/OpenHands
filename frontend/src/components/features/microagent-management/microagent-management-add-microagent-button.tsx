import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import {
  setAddMicroagentModalVisible,
  setSelectedRepository,
} from "#/state/microagent-management-slice";
import { RootState } from "#/store";
import { GitRepository } from "#/types/git";
import PlusIcon from "#/icons/plus.svg?react";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface MicroagentManagementAddMicroagentButtonProps {
  repository: GitRepository;
}

export function MicroagentManagementAddMicroagentButton({
  repository,
}: MicroagentManagementAddMicroagentButtonProps) {
  const { t } = useTranslation();

  const { addMicroagentModalVisible } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    dispatch(setAddMicroagentModalVisible(!addMicroagentModalVisible));
    dispatch(setSelectedRepository(repository));
  };

  return (
    <div onClick={handleClick}>
      <TooltipButton
        tooltip={t(I18nKey.COMMON$ADD_MICROAGENT)}
        ariaLabel={t(I18nKey.COMMON$ADD_MICROAGENT)}
        className="p-0 min-w-0 h-6 w-6 flex items-center justify-center bg-transparent cursor-pointer"
        testId="add-microagent-button"
      >
        <PlusIcon width={22} height={22} />
      </TooltipButton>
    </div>
  );
}
