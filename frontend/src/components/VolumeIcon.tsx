import React, { useState } from "react";
import { IoMdVolumeHigh, IoMdVolumeOff } from "react-icons/io";
import beep from "#/utils/beep";

function VolumeIcon(): JSX.Element {
  const [isMuted, setIsMuted] = useState(true);

  const toggleMute = () => {
    const cookieName = "audio";
    setIsMuted(!isMuted);
    if (!isMuted) {
      document.cookie = `${cookieName}=;`;
    } else {
      document.cookie = `${cookieName}=on;`;
      beep();
    }
  };

  return (
    <div
      className="cursor-pointer hover:opacity-80 transition-all"
      onClick={toggleMute}
    >
      {isMuted ? <IoMdVolumeOff size={23} /> : <IoMdVolumeHigh size={23} />}
    </div>
  );
}

export default VolumeIcon;
