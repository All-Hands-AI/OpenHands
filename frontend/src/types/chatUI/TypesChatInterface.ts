import { Message } from "../reduxSlice/TypesChatSlice";

export interface IChatBubbleProps {
  msg: Message;
}

export interface IChatInterfaceProps {
  setSettingOpen: (isOpen: boolean) => void;
}
