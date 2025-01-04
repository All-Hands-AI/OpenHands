import { Tooltip } from "@nextui-org/react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";

export function AllHandsLogoButton() {
  return (
    <Tooltip content="All Hands AI" closeDelay={100}>
      <a
        href="/"
        aria-label="All Hands Logo"
        className="w-8 h-8 rounded-full hover:opacity-80 flex items-center justify-center"
      >
        <AllHandsLogo width={34} height={23} />
      </a>
    </Tooltip>
  );
}
