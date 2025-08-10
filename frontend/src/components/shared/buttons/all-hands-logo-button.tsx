/* eslint-disable i18next/no-literal-string */
import { TooltipButton } from "./tooltip-button";

export function AllHandsLogoButton() {
  return (
    <TooltipButton tooltip="GP-KhayaL" ariaLabel="GP-KhayaL" navLinkTo="/">
      <div className="flex items-center gap-2">
        <img
          src="https://i.ibb.co/7xN0Q0w6/RDn-Sl-NCCfl-I.jpg"
          alt="GP-KhayaL Logo"
          width={34}
          height={34}
          className="rounded-sm object-cover"
        />
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">GP-KhayaL</span>
          <span className="text-[10px] opacity-70">
            Khayal Virtual Cyber Security
          </span>
        </div>
      </div>
    </TooltipButton>
  );
}
