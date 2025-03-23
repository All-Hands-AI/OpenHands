import React from "react";
import { Outlet } from "react-router";

export default function NoSidebarLayout() {
  return (
    <div className="h-screen w-screen">
      <Outlet />
    </div>
  );
}
