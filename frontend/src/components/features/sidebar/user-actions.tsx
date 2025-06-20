import React from "react";
import { UserAvatar } from "./user-avatar";
import { UserSettingsPopover } from "./user-settings-popover";

interface UserActionsProps {
  onLogout: () => void;
  user?: { avatar_url: string };
  isLoading?: boolean;
}

export function UserActions({ onLogout, user, isLoading }: UserActionsProps) {
  const [isPopoverVisible, setIsPopoverVisible] = React.useState(false);
  const closeTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    // Clear any pending close timeout
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setIsPopoverVisible(true);
  };

  const handleMouseLeave = () => {
    // Set a delay before closing to allow mouse to move to popover
    closeTimeoutRef.current = setTimeout(() => {
      setIsPopoverVisible(false);
    }, 150); // 150ms delay is standard practice
  };

  const handleLogout = () => {
    onLogout();
    setIsPopoverVisible(false);
  };

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div
      data-testid="user-actions"
      className="w-8 h-8 relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <UserAvatar
        avatarUrl={user?.avatar_url}
        onClick={() => {}} // No click handler needed for hover
        isLoading={isLoading}
      />

      <UserSettingsPopover
        isVisible={isPopoverVisible}
        onLogout={handleLogout}
      />
    </div>
  );
}
