import { useGetSettingsQuery, useSaveSettingsMutation } from '../api/slices';

export const useSettings = () => {
  const { data, isLoading, error } = useGetSettingsQuery();
  const [saveSettings, { isLoading: isSaving }] = useSaveSettingsMutation();

  return {
    data,
    isLoading,
    error,
    saveSettings,
    isSaving,
  };
};