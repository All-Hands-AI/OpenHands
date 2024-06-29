import React, { useState, ReactNode, useEffect } from "react";
import { Link } from "react-router-dom";
import { IoChevronBackOutline, IoChevronForwardOutline } from "react-icons/io5";
import {
  FaComments,
  FaRobot,
  FaUser,
  FaCog,
  FaSlack,
  FaPaperPlane,
  FaGithub,
} from "react-icons/fa";
import { FaXTwitter, FaDiscord } from "react-icons/fa6";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import CogTooth from "../assets/cog-tooth";
import AgentState from "#/types/AgentState";
import VolumeIcon from "./VolumeIcon";
import beep from "#/utils/beep";

interface LeftPushoutProps {
  onSettingsOpen: () => void;
  children?: ReactNode;
}

interface ExpandButtonProps {
  isExpanded: boolean;
  onClick: () => void;
  onSettingsOpen: () => void;
}

function ExpandButton({
  isExpanded,
  onClick,
  onSettingsOpen,
  isMuted,
  setIsMuted,
}: ExpandButtonProps & {
  isMuted: boolean;
  setIsMuted: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  return (
    <div className="w-12 bg-bg-light flex flex-col items-center justify-between h-full rounded-r-lg overflow-hidden">
      <div
        className="w-full flex-grow flex flex-col items-center justify-center cursor-pointer hover:bg-bg-editor-active transition-colors"
        onClick={onClick}
      >
        {isExpanded ? (
          <IoChevronBackOutline size={16} />
        ) : (
          <IoChevronForwardOutline size={16} />
        )}
      </div>
      <div className="w-full h-8 flex items-center justify-center cursor-pointer hover:bg-bg-editor-active transition-colors">
        <VolumeIcon isMuted={isMuted} setIsMuted={setIsMuted} />
      </div>
      <div
        className="w-full h-8 flex items-center justify-center cursor-pointer hover:bg-bg-editor-active transition-colors pb-2"
        onClick={(e) => {
          e.stopPropagation();
          onSettingsOpen();
        }}
      >
        <CogTooth />
      </div>
    </div>
  );
}

function LeftPushout({ onSettingsOpen, children }: LeftPushoutProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMuted, setIsMuted] = useState(() => {
    const audioCookie = document.cookie
      .split(";")
      .find((cookie) => cookie.trim().startsWith("audio="));
    return !(audioCookie && audioCookie.split("=")[1].trim() === "on");
  });
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  useEffect(() => {
    if (
      (curAgentState === AgentState.FINISHED ||
        curAgentState === AgentState.STOPPED ||
        curAgentState === AgentState.AWAITING_USER_INPUT ||
        curAgentState === AgentState.ERROR) &&
      !isMuted
    ) {
      beep();
    }
  }, [curAgentState, isMuted]);

  const socialLinks = [
    {
      icon: <FaSlack />,
      name: "Slack - Join us!",
      url: "https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA",
    },
    {
      icon: <FaGithub />,
      name: "GitHub",
      url: "https://www.github.com/OpenDevin",
    },
  ];

  const navItems = [
    { icon: <FaComments />, label: "All Chats", to: "/chats" },
    { icon: <FaRobot />, label: "Your Prompts", to: "/prompts" },
    { icon: <FaUser />, label: "Profile", to: "/profile" },
    { icon: <FaCog />, label: "Settings", action: onSettingsOpen },
    { icon: <FaPaperPlane />, label: "Send feedback", to: "/feedback" },
  ];

  const footerLinks = [
    { text: "About", url: "https://www.all-hands.dev/about" },
    { text: "Careers", url: "https://www.all-hands.dev/careers" },
    { text: "Contact", url: "https://www.all-hands.dev/contact" },
    { text: "Privacy policy", url: "https://www.all-hands.dev/privacy" },
    { text: "Terms of service", url: "https://www.all-hands.dev/terms" },
  ];

  return (
    <div
      className={`flex h-full transition-all duration-200 ${
        isExpanded ? "w-64" : "w-8"
      }`}
    >
      <div
        className={`bg-bg-dark h-full overflow-hidden transition-all duration-200 flex flex-col justify-between ${
          isExpanded ? "w-[calc(100%-1.5rem)]" : "w-0"
        }`}
      >
        {isExpanded && (
          <>
            <div className="flex-grow overflow-y-auto p-2">
              {children}
              {navItems.map((item, index) =>
                item.action ? (
                  <button
                    key={index}
                    type="button"
                    className="flex items-center w-full px-4 py-2 text-sm text-foreground hover:bg-bg-editor-active rounded transition-colors"
                    onClick={item.action}
                  >
                    {React.cloneElement(item.icon, { className: "mr-3" })}
                    {item.label}
                  </button>
                ) : (
                  <Link
                    key={index}
                    to={item.to}
                    className="flex items-center w-full px-4 py-2 text-sm text-foreground hover:bg-bg-editor-active rounded transition-colors"
                  >
                    {React.cloneElement(item.icon, { className: "mr-3" })}
                    {item.label}
                  </Link>
                ),
              )}
            </div>
            <div className="p-4 space-y-2">
              {socialLinks.map((link, index) => (
                <button
                  key={index}
                  type="button"
                  className="w-full px-4 py-2 text-sm text-foreground bg-bg-light hover:bg-bg-editor-active rounded transition-colors flex items-center justify-start"
                  onClick={() => window.open(link.url, "_blank")}
                >
                  {React.cloneElement(link.icon, { className: "mr-2" })}
                  {link.name}
                </button>
              ))}
              <div className="flex justify-center space-x-4 mt-4">
                <a
                  href="https://twitter.com/allhandsdev"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Twitter"
                >
                  <FaXTwitter className="text-white hover:text-blue-400 transition-colors" />
                </a>
                <a
                  href="https://discord.gg/ESHStjSjD4"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Discord"
                >
                  <FaDiscord className="text-white hover:text-indigo-4000 transition-colors" />
                </a>
              </div>
              <div className="text-xs text-text-editor-base mt-4 text-center">
                {footerLinks.map((link, index) => (
                  <React.Fragment key={index}>
                    {index > 0 && " · "}
                    <a href={link.url} className="hover:underline">
                      {link.text}
                    </a>
                  </React.Fragment>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
      <ExpandButton
        isExpanded={isExpanded}
        onClick={toggleExpand}
        onSettingsOpen={onSettingsOpen}
        isMuted={isMuted}
        setIsMuted={setIsMuted}
      />
    </div>
  );
}

export default LeftPushout;
