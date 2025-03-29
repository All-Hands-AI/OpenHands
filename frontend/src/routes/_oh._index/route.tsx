import React from "react";
import { useNavigate } from "react-router";
import { WelcomeHeader } from "#/components/features/welcome/welcome-header";
import { ConnectToRepo } from "#/components/features/welcome/connect-to-repo";
import { SuggestedTasks } from "#/components/features/welcome/suggested-tasks";
import { LaunchFromScratchButton } from "#/components/features/welcome/launch-from-scratch-button";

function Home() {
  const navigate = useNavigate();

  const handleLaunchFromScratch = () => {
    // This would typically start a new project from scratch
    // For now, we'll just navigate to the workspace
    navigate("/workspace");
  };

  return (
    <div
      data-testid="home-screen"
      className="bg-[#1E1E1E] h-full rounded-xl flex flex-col relative overflow-y-auto p-6"
    >
      <div className="flex flex-col w-full">
        {/* Welcome Header */}
        <WelcomeHeader />

        {/* Divider */}
        <div className="w-full h-px bg-[#525252] my-8" />

        {/* Main Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column - Connect to Repo */}
          <div className="flex flex-col">
            <ConnectToRepo>
              <select className="w-full bg-[#2A2A2A] text-white p-2 rounded-md border border-[#525252]">
                <option>Select a Repo</option>
              </select>
            </ConnectToRepo>
          </div>

          {/* Right Column - Suggested Tasks */}
          <div className="flex flex-col">
            <SuggestedTasks />
          </div>
        </div>
      </div>

      {/* Launch From Scratch Button - Fixed at the top right */}
      <div className="absolute top-6 right-6 w-48">
        <LaunchFromScratchButton onClick={handleLaunchFromScratch} />
      </div>
    </div>
  );
}

export default Home;
