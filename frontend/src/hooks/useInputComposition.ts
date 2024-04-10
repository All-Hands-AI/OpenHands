import { useState } from "react";

const useInputComposition = () => {
  const [isComposing, setIsComposing] = useState(false);
  const handleCompositionStart = () => {
    setIsComposing(true);
  };
  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  return {
    isComposing,
    onCompositionStart: handleCompositionStart,
    onCompositionEnd: handleCompositionEnd,
  };
};

export default useInputComposition;
