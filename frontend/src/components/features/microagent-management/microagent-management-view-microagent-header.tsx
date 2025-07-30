import { useSelector, useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { BrandButton } from "../settings/brand-button";
import { getProviderName, constructMicroagentUrl } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import { setUpdateMicroagentModalVisible } from "#/state/microagent-management-slice";

export function MicroagentManagementViewMicroagentHeader() {
  const { t } = useTranslation();
  const dispatch = useDispatch();

  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent } = selectedMicroagentItem ?? {};

  if (!microagent || !selectedRepository) {
    return null;
  }

  // Construct the microagent URL
  const microagentUrl = constructMicroagentUrl(
    selectedRepository.git_provider,
    selectedRepository.full_name,
    microagent.path,
  );

  const handleLearnSomethingNew = () => {
    dispatch(setUpdateMicroagentModalVisible(true));
  };

  return (
    <div className="flex items-center justify-between pb-2">
      <span className="text-sm text-[#ffffff99]">
        {selectedRepository.full_name}
      </span>
      <div className="flex items-center justify-end gap-2">
        <a href={microagentUrl} target="_blank" rel="noopener noreferrer">
          <BrandButton
            type="button"
            variant="secondary"
            testId="edit-in-git-button"
            className="py-1 px-2"
          >
            {`${t(I18nKey.COMMON$EDIT_IN)} ${getProviderName(selectedRepository.git_provider)}`}
          </BrandButton>
        </a>
        <BrandButton
          type="button"
          variant="primary"
          onClick={handleLearnSomethingNew}
          testId="learn-button"
          className="py-1 px-2"
        >
          {t(I18nKey.COMMON$LEARN_SOMETHING_NEW)}
        </BrandButton>
      </div>
    </div>
  );
}
