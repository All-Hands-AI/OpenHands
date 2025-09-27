import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import ListIcon from "#/icons/list.svg?react";
import { UnifiedButton } from "#/ui/unified-button/unified-button";
import { cn } from "#/utils/utils";

interface ConversationPanelButtonProps {
  isOpen: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function ConversationPanelButton({
  isOpen,
  onClick,
  disabled = false,
}: ConversationPanelButtonProps) {
  const { t } = useTranslation();

  return (
    <UnifiedButton
      as="NavLink"
      to="#"
      withTooltip
      tooltipContent={t(I18nKey.SIDEBAR$CONVERSATIONS)}
      ariaLabel={t(I18nKey.SIDEBAR$CONVERSATIONS)}
      onClick={onClick}
      testId="toggle-conversation-panel"
      disabled={disabled}
      activeClassName="text-white"
      inactiveClassName="text-[#B1B9D3]"
      tooltipProps={{
        placement: "right",
      }}
      className="bg-transparent hover:bg-transparent"
    >
      <ListIcon
        width={24}
        height={24}
        className={cn(
          "cursor-pointer",
          isOpen ? "text-white" : "text-[#B1B9D3]",
          disabled && "opacity-50",
        )}
      />
    </UnifiedButton>
  );
}
