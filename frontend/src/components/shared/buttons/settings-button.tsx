import CogTooth from "#/assets/cog-tooth";

interface SettingsButtonProps {
  onClick: () => void;
}

export function SettingsButton({ onClick }: SettingsButtonProps) {
  return (
    <button
      type="button"
      aria-label="Settings"
      className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
      onClick={onClick}
    >
      <CogTooth />
    </button>
  );
}
