import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function Browser(): JSX.Element {
  const url = useSelector((state: RootState) => state.browser.url);
  return (
    <div className="h-full m-2 bg-bg-workspace mockup-browser">
      <div className="mockup-browser-toolbar">
        <div className="input">{url}</div>
      </div>
    </div>
  );
}

export default Browser;
