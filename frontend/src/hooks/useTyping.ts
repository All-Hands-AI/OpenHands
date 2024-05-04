import React from "react";

export const useTyping = (text: string) => {
  const [message, setMessage] = React.useState(text[0]);

  const advance = () =>
    setTimeout(() => {
      if (message.length < text.length) {
        setMessage(text.slice(0, message.length + 1));
      }
    }, 10);

  React.useEffect(() => {
    const timeout = advance();

    return () => {
      clearTimeout(timeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message]);

  return message;
};
