import React from "react";
import styles from "./index.module.css";

export function Demo() {
  const videoRef = React.useRef<HTMLVideoElement>(null);

  return (
      <video
        playsInline
        autoPlay={true}
        loop
        className={styles.demo}
        muted
        onMouseOver={() => (videoRef.current.controls = true)}
        onMouseOut={() => (videoRef.current.controls = false)}
        ref={videoRef}
      >
        <source src="img/teaser.mp4" type="video/mp4"></source>
      </video>
  );
}
