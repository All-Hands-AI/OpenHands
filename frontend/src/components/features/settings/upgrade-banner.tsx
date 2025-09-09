import { UpgradeButton } from "./upgrade-button";
import { BannerMessage } from "./banner-message";
import { cn } from "#/utils/utils";

interface UpgradeBannerProps {
  message: string;
  onUpgradeClick?: () => void;
  className?: string;
}

export function UpgradeBanner({
  message,
  onUpgradeClick,
  className,
}: UpgradeBannerProps) {
  return (
    <div
      className={cn(
        "bg-primary text-base flex items-center justify-center gap-3 p-2 w-full",
        className,
      )}
      data-testid="upgrade-banner"
    >
      <BannerMessage message={message} />
      <UpgradeButton onClick={onUpgradeClick} />
    </div>
  );
}
