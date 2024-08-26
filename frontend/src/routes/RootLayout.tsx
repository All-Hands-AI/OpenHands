import React from "react";
import { Outlet } from "react-router-dom";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";

function RootLayout() {
  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <AllHandsLogo width={34} height={23} />
        <nav className="py-[18px] flex flex-col gap-[18px]">
          <div className="w-8 h-8 rounded-full bg-red-100" />
          <div className="w-8 h-8 rounded-full bg-green-100" />
          <div className="w-8 h-8 rounded-full bg-blue-100" />
        </nav>
      </aside>
      <div className="w-full">
        <Outlet />
      </div>
    </div>
  );
}

export default RootLayout;
