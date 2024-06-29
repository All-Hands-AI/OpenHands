import React from "react";
import { IoMdVolumeHigh, IoMdVolumeOff } from "react-icons/io";
import beep from "#/utils/beep";

interface VolumeIconProps {
  isMuted: boolean;
  setIsMuted: React.Dispatch<React.SetStateAction<boolean>>;
}
function VolumeIcon({ isMuted, setIsMuted }: VolumeIconProps): JSX.Element {
  const toggleMute = () => {
    const cookieName = "audio";
    setIsMuted((prevMuted) => {
      const newMuted = !prevMuted;
      if (newMuted) {
        document.cookie = `${cookieName}=;`;
      } else {
        document.cookie = `${cookieName}=on;`;
        beep();
      }
      return newMuted;
    });
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
