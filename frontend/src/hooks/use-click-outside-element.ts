import React from "react";

/**
 * Hook to call a callback function when an element is clicked outside
 * @param callback The callback function to call when the element is clicked outside
 */
export const useClickOutsideElement = <T extends HTMLElement>(
  callback: () => void,
) => {
  const ref = React.useRef<T>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    setTimeout(() => {
      document.addEventListener("click", handleClickOutside);
    }, 0);

    return () => document.removeEventListener("click", handleClickOutside);
  }, [callback]);

  return ref;
};
