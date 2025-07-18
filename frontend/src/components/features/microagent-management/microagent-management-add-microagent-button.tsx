import { useTranslation } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { setAddMicroagentModalVisible } from "#/state/microagent-management-slice";
import { RootState } from "#/store";

export function MicroagentManagementAddMicroagentButton() {
  const { t } = useTranslation();

  const { addMicroagentModalVisible } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();

  const handleClick = () => {
    dispatch(setAddMicroagentModalVisible(!addMicroagentModalVisible));
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
