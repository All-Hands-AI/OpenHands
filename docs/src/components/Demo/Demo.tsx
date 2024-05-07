import React from "react";
import styles from "./index.module.css";

export function Demo() {
  const videoRef = React.useRef<HTMLVideoElement>(null);

  return (
    <div
      style={{ paddingBottom: "30px", paddingTop: "20px", textAlign: "center" }}
    >
      <img src="img/demo.gif" type="video/mp4"></img>
    </div>
  );
}
