import { useEffect, type PropsWithChildren } from "react";
import { ToastContainer } from "react-toastify";

export const ToastManager = (props: PropsWithChildren) => {
  useEffect(() => {
    const style = document.createElement("style");
    // Link to all variables
    // https://fkhadra.github.io/react-toastify/how-to-style/#override-css-variables
    style.innerHTML = `
      :root {
        --toastify-toast-padding: 0;
        --toastify-toast-bd-radius: 0;
        --toastify-toast-shadow: none;
        --toastify-toast-min-height: 0;
        --toastify-toast-width: initial;
        --toastify-color-light: transparent;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <>
      <ToastContainer
        closeButton={false}
        hideProgressBar
        autoClose={false}
        position="bottom-right"
      />
      {props.children}
    </>
  );
};
