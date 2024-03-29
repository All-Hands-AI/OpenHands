import React from "react";
import "./css/Browser.css";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function Browser(): JSX.Element {
  const url = useSelector((state: RootState) => state.browser.url);
  return (
    <div className="mockup-browser">
      <div className="mockup-browser-toolbar">
        <div className="input">{url}</div>
      </div>
    </div>
  );
}

export default Browser;
