import React from "react";
import { Card, CardBody } from "@nextui-org/react";
import assistantAvatar from "../../assets/assistant-avatar.png";
import userAvatar from "../../assets/user-avatar.png";
import { IChatBubbleProps } from "../../types/chatUI/TypesChatInterface";

function ChatBubble({ msg }: IChatBubbleProps): JSX.Element {
  return (
    <div className="flex mb-2.5 pr-5 pl-5">
      <div
        className={`flex mt-2.5 mb-0 min-w-0 ${msg?.sender === "user" && "flex-row-reverse ml-auto"}`}
      >
        <img
          src={msg?.sender === "user" ? userAvatar : assistantAvatar}
          alt={`${msg?.sender} avatar`}
          className="w-[40px] h-[40px] mx-2.5"
        />
        <Card className={`${msg?.sender === "user" ? "bg-primary-100" : ""}`}>
          <CardBody>{msg?.content}</CardBody>
        </Card>
      </div>
    </div>
  );
}
export default ChatBubble;
