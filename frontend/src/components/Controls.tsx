import AgentControlBar from "#/components/AgentControlBar";
import AgentStatusBar from "#/components/AgentStatusBar";
import VolumeIcon from "#/components/VolumeIcon";
import CogTooth from "#/assets/cog-tooth";

interface Props {
  setSettingOpen: (isOpen: boolean) => void;
}

function Controls({ setSettingOpen }: Props): JSX.Element {
  return (
    <div className="flex w-full p-4 bg-neutral-900 items-center shrink-0 justify-between">
      <div className="flex items-center gap-4">
        <AgentControlBar />
      </div>
      <AgentStatusBar />

      <div style={{ display: "flex", alignItems: "center" }}>
        <div style={{ marginRight: "8px" }}>
          <VolumeIcon />
        </div>
        <div
          className="cursor-pointer hover:opacity-80 transition-all"
          onClick={() => setSettingOpen(true)}
        >
          <CogTooth />
        </div>
      </div>
    </div>
  );
}

export default Controls;
