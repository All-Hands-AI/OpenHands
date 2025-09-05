import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import PlusIcon from "#/icons/u-plus.svg?react";
import { HeaderWithIcon } from "#/ui/header-with-icon";
import { DescriptionText } from "#/ui/description-text";
import { CreateConversationButton } from "./create-conversation-button";
import { Card } from "#/ui/card";

export function NewConversation() {
  const { t } = useTranslation();

  return (
    <Card>
      <HeaderWithIcon icon={<PlusIcon width={17} height={14} />}>
        {t(I18nKey.COMMON$START_FROM_SCRATCH)}
      </HeaderWithIcon>
      <DescriptionText>
        {t(I18nKey.HOME$NEW_PROJECT_DESCRIPTION)}
      </DescriptionText>
      <CreateConversationButton />
    </Card>
  );
}
