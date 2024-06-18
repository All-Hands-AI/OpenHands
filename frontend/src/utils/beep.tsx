import React from "react";
const beep = () => {
  const snd = new Audio("/beep.wav");
  snd.addEventListener("canplaythrough", () => snd.play());
  snd.addEventListener("error", (e) =>
    console.error("Audio file could not be loaded", e),
  );
};

export default beep;
