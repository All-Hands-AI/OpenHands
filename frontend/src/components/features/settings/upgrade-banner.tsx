import { UpgradeButton } from "./upgrade-button";
import { BannerMessage } from "./banner-message";

interface UpgradeBannerProps {
  message: string;
  onUpgradeClick?: () => void;
}

export function UpgradeBanner({ message, onUpgradeClick }: UpgradeBannerProps) {
  return (
    <div
      className="bg-[#c5ba7d] box-border content-stretch flex items-center justify-center p-[8px] relative w-full"
      data-testid="upgrade-banner"
    >
      <div className="box-border content-stretch flex gap-[11px] items-center justify-center min-h-6 px-1 py-0 relative shrink-0">
        <BannerMessage message={message} />
        <UpgradeButton onClick={onUpgradeClick} />
      </div>
    </div>
  );
}
