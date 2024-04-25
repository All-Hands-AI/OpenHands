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
          src="https://github-production-user-asset-6210df.s3.amazonaws.com/38853559/318638664-71a472cc-df34-430c-8b1d-4d7286c807c9.webm?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20240426%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240426T001612Z&X-Amz-Expires=300&X-Amz-Signature=8ab9974b557a380fcd8667beb362af7d5584357c182ae850e4e6244da53bf5fb&X-Amz-SignedHeaders=host&actor_id=5690524&key_id=0&repo_id=771302083"
          type="video/webm"
        ></source>
      </video>
    </div>
  );
}
