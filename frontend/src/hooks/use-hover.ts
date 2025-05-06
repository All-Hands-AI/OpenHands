import { useState } from "react";

export function useHover() {
  const [isHovering, setIsHovering] = useState(false);

  const hoverProps = {
    onMouseEnter: () => setIsHovering(true),
    onMouseLeave: () => setIsHovering(false),
  };

  return [isHovering, hoverProps] as const;
}
