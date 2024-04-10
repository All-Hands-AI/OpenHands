import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function Browser(): JSX.Element {
  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  );

  const imgSrc =
    screenshotSrc && screenshotSrc.startsWith("data:image/png;base64,")
      ? screenshotSrc
      : `data:image/png;base64,${screenshotSrc || ""}`;

  return (
    <div className="h-full m-2 bg-neutral-700 mockup-browser">
      <div className="mockup-browser-toolbar">
        <div className="input">{url}</div>
      </div>
      {screenshotSrc ? (
        <img
          src={imgSrc}
          alt="Browser Screenshot"
          style={{ maxWidth: "100%", height: "auto" }}
        />
      ) : (
        <div>No screenshot available.</div>
      )}
    </div>
  );
}

export default Browser;
