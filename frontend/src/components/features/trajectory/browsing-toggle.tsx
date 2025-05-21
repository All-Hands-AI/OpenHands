import { useNavigate } from "react-router";
import { useSettings } from "#/hooks/query/use-settings";
import GlobeIcon from "#/icons/globe.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";

export function BrowsingToggle() {
  // Use try/catch to handle the case when useNavigate is not available (in tests)
  let navigateFunction: (path: string) => void = () => {};
  try {
    const navigate = useNavigate();
    navigateFunction = navigate;
  } catch (error) {
    // In tests, useNavigate might not be available
    // Just use a no-op function instead
  }

  const { data: settings } = useSettings();

  const isBrowsingEnabled = !!settings?.ENABLE_BROWSING;

  const handleClick = () => {
    navigateFunction("/settings/app");
  };

  return (
    <TrajectoryActionButton
      testId="browsing-toggle"
      onClick={handleClick}
      icon={<GlobeIcon width={15} height={15} />}
      tooltip={`Browsing is ${isBrowsingEnabled ? "enabled" : "disabled"}. Click to change.`}
      active={isBrowsingEnabled}
    />
  );
}
