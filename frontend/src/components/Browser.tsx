import React from "react";
import "./Browser.css";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function Browser(): JSX.Element {
  const url = useSelector((state: RootState) => state.browser.url);
  return (
    <div
      className="mockup-browser"
      style={{
        background: "black",
        padding: "1rem",
        height: "90%",
        margin: "1rem",
        borderRadius: "1rem",
      }}
    >
      <div className="mockup-browser-toolbar">
        <div className="input">{url}</div>
      </div>
    </div>
  );
}

export default Browser;
