import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import {
  setAddMicroagentModalVisible,
  setSelectedRepository,
} from "#/state/microagent-management-slice";
import { RootState } from "#/store";
import { GitRepository } from "#/types/git";

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

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    dispatch(setAddMicroagentModalVisible(!addMicroagentModalVisible));
    dispatch(setSelectedRepository(repository));
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className="translate-y-[-1px]"
      data-testid="add-microagent-button"
    >
      <span className="text-sm font-normal leading-5 text-[#8480FF] cursor-pointer hover:text-[#6C63FF] transition-colors duration-200">
        {t(I18nKey.COMMON$ADD_MICROAGENT)}
      </span>
    </button>
  );
}
