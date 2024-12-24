import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "#/store";
import { Settings } from "#/api/open-hands.types";
import {
  loadSettings,
  storeSettings,
  updateSettings,
} from "#/state/settings-slice";

export function useSettings() {
  const dispatch = useDispatch<AppDispatch>();
  const { settings, isLoading, error } = useSelector(
    (state: RootState) => state.settings,
  );

  useEffect(() => {
    dispatch(loadSettings());
  }, [dispatch]);

  const saveSettings = async (newSettings: Settings) => {
    await dispatch(storeSettings(newSettings)).unwrap();
  };

  const updateSettingsLocally = (newSettings: Partial<Settings>) => {
    dispatch(updateSettings(newSettings));
  };

  return {
    settings,
    isLoading,
    error,
    saveSettings,
    updateSettingsLocally,
  };
}
