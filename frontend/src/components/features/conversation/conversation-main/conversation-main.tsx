import { useSelector } from "react-redux";
import { useWindowSize } from "@uidotdev/usehooks";
import { RootState } from "#/store";
import { MobileLayout } from "./mobile-layout";
import { DesktopLayoutWithPanel } from "./desktop-layout-with-panel";
import { DesktopLayoutWithoutPanel } from "./desktop-layout-without-panel";

export function ConversationMain() {
  const { width } = useWindowSize();
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  if (width && width <= 1024) {
    return <MobileLayout isRightPanelShown={isRightPanelShown} />;
  }

  if (isRightPanelShown) {
    return <DesktopLayoutWithPanel isRightPanelShown={isRightPanelShown} />;
  }

  return <DesktopLayoutWithoutPanel isRightPanelShown={isRightPanelShown} />;
}
