import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";

interface AllHandsLogoButtonProps {
  onClick: () => void;
}

export function AllHandsLogoButton({ onClick }: AllHandsLogoButtonProps) {
  return (
    <button type="button" aria-label="All Hands Logo" onClick={onClick}>
      <AllHandsLogo width={34} height={23} />
    </button>
  );
}
