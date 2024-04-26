import React from "react";
import styles from "./index.module.css";

export function Demo() {
  const videoRef = React.useRef<HTMLVideoElement>(null);

  return (
    <div
      style={{ paddingBottom: "30px", paddingTop: "20px", textAlign: "center" }}
    >
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
        <source
          src="https://private-user-images.githubusercontent.com/38853559/318638664-71a472cc-df34-430c-8b1d-4d7286c807c9.webm?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MTQwOTEyNTAsIm5iZiI6MTcxNDA5MDk1MCwicGF0aCI6Ii8zODg1MzU1OS8zMTg2Mzg2NjQtNzFhNDcyY2MtZGYzNC00MzBjLThiMWQtNGQ3Mjg2YzgwN2M5LndlYm0_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQwNDI2JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MDQyNlQwMDIyMzBaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT02YTQxNmE4ZjIzMDFkZTQ0ZTUxYjUzNGI5MmFhMDdhMzU4MmM1YTQyMTU4MmRkNDZmZmZkMWYyY2EzMzc1ZjVjJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.4dj-ZQvPwW_76Mh81XXD7CkZcXrs-lsh-R6BrmA-_gY"
          type="video/webm"
        ></source>
      </video>
    </div>
  );
}
