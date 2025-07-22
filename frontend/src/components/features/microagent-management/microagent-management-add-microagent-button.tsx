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
      className="text-sm font-normal text-[#8480FF] cursor-pointer"
      onClick={handleClick}
    >
      {t(I18nKey.COMMON$ADD_MICROAGENT)}
    </button>
  );
}
