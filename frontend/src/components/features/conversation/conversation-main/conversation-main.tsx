import { useSelector } from "react-redux";
import { useWindowSize } from "@uidotdev/usehooks";
import { RootState } from "#/store";
import { MobileLayout } from "./mobile-layout";
import { DesktopLayout } from "./desktop-layout";

export function ConversationMain() {
  const { width } = useWindowSize();
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  if (width && width <= 1024) {
    return <MobileLayout isRightPanelShown={isRightPanelShown} />;
  }

  return <DesktopLayout isRightPanelShown={isRightPanelShown} />;
}
