import { useNavigate } from "react-router";
import { useSettings } from "#/hooks/query/use-settings";
import GlobeIcon from "#/icons/globe.svg?react";
import { TrajectoryActionButton } from "#/components/shared/buttons/trajectory-action-button";

export function BrowsingToggle() {
  const navigate = useNavigate();
  const { data: settings } = useSettings();
  
  const isBrowsingEnabled = !!settings?.ENABLE_BROWSING;
  
  const handleClick = () => {
    navigate("/settings/app");
  };

  return (
    <TrajectoryActionButton
      testId="browsing-toggle"
      onClick={handleClick}
      icon={<GlobeIcon width={15} height={15} />}
      tooltip={`Browsing is ${isBrowsingEnabled ? 'enabled' : 'disabled'}. Click to change.`}
      active={isBrowsingEnabled}
    />
  );
}