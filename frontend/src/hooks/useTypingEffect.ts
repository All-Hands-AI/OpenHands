import { useEffect, useState } from "react";
import { Message } from "../state/chatSlice";
/**
 * hook to be used for typing chat effect
 */
export const useTypingEffect = (
  strings: string[] = [""],
  {
    loop = false,
    playbackRate = 0.1,
    setTypingActive = () => {},
    addAssistantMessageToChat = () => {},
    takeOneAndType = () => {},
    typeThis = { content: "", sender: "assistant" },
  }: {
    loop?: boolean;
    playbackRate?: number;
    setTypingActive?: (bool: boolean) => void;
    addAssistantMessageToChat?: (msg: Message) => void;
    takeOneAndType?: () => void;
    typeThis?: Message;
  } = {
    loop: false,
    playbackRate: 0.1,
    setTypingActive: () => {},
    addAssistantMessageToChat: () => {},
    takeOneAndType: () => {},
    typeThis: { content: "", sender: "assistant" },
  },
) => {
  // eslint-disable-next-line prefer-const
  let [{ stringIndex, characterIndex }, setState] = useState<{
    stringIndex: number;
    characterIndex: number;
  }>({
    stringIndex: 0,
    characterIndex: 0,
  });

  let timeoutId: number;
  const emulateKeyStroke = () => {
    // eslint-disable-next-line no-plusplus
    characterIndex++;
    if (characterIndex === strings[stringIndex].length) {
      characterIndex = 0;
      // eslint-disable-next-line no-plusplus
      stringIndex++;
      if (stringIndex === strings.length) {
        if (!loop) {
          setTypingActive(false);
          addAssistantMessageToChat(typeThis);
          takeOneAndType();
          return;
        }
        stringIndex = 0;
      }
      timeoutId = window.setTimeout(emulateKeyStroke, 100 * playbackRate);
    } else if (characterIndex === strings[stringIndex].length - 1) {
      timeoutId = window.setTimeout(emulateKeyStroke, 2000 * playbackRate);
    } else {
      timeoutId = window.setTimeout(emulateKeyStroke, 100 * playbackRate);
    }
    setState({
      characterIndex,
      stringIndex,
    });
  };

  useEffect(() => {
    emulateKeyStroke();
    return () => {
      window.clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nonBreakingSpace = "\u00A0";
  return strings[stringIndex].slice(0, characterIndex + 1) || nonBreakingSpace;
};
