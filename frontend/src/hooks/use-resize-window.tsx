import { useEffect, useState } from "react";

export function useResizeWindow() {
  const [width, setWidth] = useState(window.innerWidth);

  function handleResize() {
    setWidth(window.innerWidth);
  }

  useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const isSmallerDevice = width <= 768;

  return { width, isSmallerDevice };
}
